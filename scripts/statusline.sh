#!/usr/bin/env bash

# Claude Code status line - reads the session JSON on stdin, prints one line:
#   user ➜ dir (branch) │ ctx bar │ cache cost · session cost │ cache warm/cold timer
# wired in .claude/settings.json; display only - agents never see this output
# no `set -e` and no logging.sh: a status line must always print and exit 0, never write logs or errors
exec 2>/dev/null

# cache TTL override in seconds (default: TTL seen in the transcript, else 1h)
CACHE_TTL="${CLAUDE_CACHE_TTL:-}"

command -v jq >/dev/null || { echo "statusline.sh needs jq (apt install jq)"; exit 0; }

RST=$'\033[0m'; DIM=$'\033[2m'; BLD=$'\033[1m'
RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YEL=$'\033[0;33m'; CYN=$'\033[0;36m'
BLUE_B=$'\033[1;34m'; RED_B=$'\033[1;31m'

# fmt <n>: 950 -> 950, 51234 -> 51k, 1234567 -> 1.23M
fmt() { awk -v n="$1" 'BEGIN { if (n >= 1e6) printf "%.3gM", n / 1e6; else if (n >= 1e3) printf "%.0fk", n / 1e3; else printf "%d", n }'; }

# dur <seconds>: 2520 -> 42m, 3900 -> 1h5m
dur() {
    local m=$(( $1 / 60 ))
    if [ "$m" -ge 60 ]; then echo "$(( m / 60 ))h$(( m % 60 ))m"; else echo "${m}m"; fi
}

# bar <percent> <width>: filled/empty cells, clamped to 0..width
bar() {
    local n=$(( ($1 * $2 + 50) / 100 )) i out=""
    [ "$n" -gt "$2" ] && n=$2
    [ "$n" -lt 0 ] && n=0
    for (( i = 0; i < $2; i++ )); do
        if [ "$i" -lt "$n" ]; then out+="█"; else out+="░"; fi
    done
    printf '%s' "$out"
}

# pct_color <percent> <warn> <crit> [inv]: green/yellow/red by threshold (inv: high is good)
pct_color() {
    local p=$1
    [ -n "${4:-}" ] && p=$(( 100 - p ))
    if [ "$p" -ge "$3" ]; then echo "$RED"; elif [ "$p" -ge "$2" ]; then echo "$YEL"; else echo "$GRN"; fi
}

input="$(cat)"
model="$(echo "$input" | jq -r '.model.id // ""')"
transcript="$(echo "$input" | jq -r '.transcript_path // empty')"

# --- prompt: user ➜ dir (branch), mirrors the devcontainer bash prompt ---
dir="$(echo "$input" | jq -r '.workspace.current_dir // .cwd')"
branch="$(git -C "$dir" --no-optional-locks symbolic-ref --short HEAD || git -C "$dir" --no-optional-locks rev-parse --short HEAD)"
printf '%s%s %s➜ %s%s%s' "$GRN" "$(whoami)" "$RST" "$BLUE_B" "$dir" "$RST"
[ -n "$branch" ] && printf ' %s(%s%s%s)%s' "$CYN" "$RED_B" "$branch" "$CYN" "$RST"

# --- token totals from the transcript (one jq pass) ---
# out: 5m cache writes, 1h cache writes, cache reads, uncached input, last turn's context, last timestamp, TTL in use
stats=""
if [ -n "$transcript" ] && [ -r "$transcript" ]; then
    stats="$(jq -R -n -r '
        # streamed entries repeat per message id - keep the last one
        reduce (inputs | fromjson? | select(type == "object" and .type == "assistant" and (.message.usage | type) == "object")) as $e
            ({usage: {}, last: null, ttl: ""};
             .usage[$e.message.id // $e.uuid // (.usage | length | tostring)] = $e.message.usage
             | .last = $e
             # TTL in use = TTL of the most recent cache write
             | ($e.message.usage.cache_creation // {}) as $cc
             | .ttl = if ($cc.ephemeral_1h_input_tokens // 0) > 0 then "3600"
                      elif ($cc.ephemeral_5m_input_tokens // 0) > 0 then "300"
                      else .ttl end)
        | select(.last != null)
        | [.usage[]] as $all
        | def total(f): [$all[] | f // 0] | add // 0;
          .last.message.usage as $lu
        | [ total(.cache_creation | objects | .ephemeral_5m_input_tokens),
            # older entries have no cache_creation breakdown - count their writes as 1h
            total(if (.cache_creation | type) == "object" then .cache_creation.ephemeral_1h_input_tokens
                  else .cache_creation_input_tokens end),
            total(.cache_read_input_tokens),
            total(.input_tokens),
            ($lu.input_tokens // 0) + ($lu.cache_read_input_tokens // 0) + ($lu.cache_creation_input_tokens // 0),
            .last.timestamp // "",
            .ttl ]
        | @tsv' "$transcript")"
fi
# ttl stays last: tab is IFS whitespace, so an empty field mid-line would shift the rest
IFS=$'\t' read -r write_5m write_1h cache_read uncached last_ctx last_ts seen_ttl <<< "$stats"

# USD per million tokens: <input> <cache read>; cache writes cost 1.25x (5m TTL) or 2x (1h TTL) input
case "$model" in
    *opus-5-5*)   price=(4 0.2) ;;
    *sonnet-5-5*) price=(2 0.1) ;;
    *fable-5-2*)  price=(8 0.2) ;;
    *haiku-5-5*)  price=(0.1 0.01) ;;
    *)            price=(4 0.2) ;;
esac

segs=()

# --- 1. context window ---
read -r used size pct session_cost <<< "$(echo "$input" | jq -r '[
    (.context_window.current_usage // null
        | if . then (.input_tokens // 0) + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0) else null end),
    .context_window.context_window_size,
    .context_window.used_percentage,
    .cost.total_cost_usd
    ] | map(. // "-") | join(" ")')"
{ [ "$used" = "-" ] || [ -z "$used" ]; } && used="$last_ctx"
if [ -n "$used" ]; then
    ctx="$(fmt "$used")"
    if [ -n "$size" ] && [ "$size" != "-" ]; then
        ctx+="/$(fmt "$size")"
        { [ -z "$pct" ] || [ "$pct" = "-" ]; } && pct="$(awk -v u="$used" -v z="$size" 'BEGIN { if (z > 0) printf "%.0f", 100 * u / z }')"
    fi
    if [ -n "$pct" ] && [ "$pct" != "-" ]; then
        p="$(printf '%.0f' "$pct")"
        segs+=("${DIM}ctx${RST} $(pct_color "$p" 70 90)$(bar "$p" 10)${RST} ${BLD}${p}%${RST} ${DIM}${ctx}${RST}")
    else
        segs+=("${DIM}ctx ${ctx}${RST}")
    fi
fi

# --- 2. cache cost estimate + session total ---
s=""
if [ -n "$write_5m" ]; then
    read -r cache_cost write_cost read_cost hit <<< "$(awk -v w5="$write_5m" -v w1="$write_1h" -v r="$cache_read" -v u="$uncached" \
        -v p_in="${price[0]}" -v p_read="${price[1]}" 'BEGIN {
        wc = (w5 * 1.25 + w1 * 2) * p_in / 1e6; rc = r * p_read / 1e6; d = r + w5 + w1 + u
        printf "%.2f %.2f %.2f %d", wc + rc, wc, rc, (d > 0) ? int(100 * r / d + 0.5) : -1 }')"
    s="${DIM}cache${RST} ${BLD}\$${cache_cost}${RST} ${DIM}(${RST}${YEL}↑\$${write_cost}${RST} ${DIM}write ·${RST} ${CYN}↓\$${read_cost}${RST} ${DIM}read)${RST}"
    # hit rate: high is good, so the color scale is inverted
    [ "$hit" -ge 0 ] && s+=" ${DIM}hit${RST} $(pct_color "$hit" 30 60 inv)$(bar "$hit" 5) ${hit}%${RST}"
fi
if [ -n "$session_cost" ] && [ "$session_cost" != "-" ]; then
    s="${s:+$s ${DIM}·${RST} }${DIM}session${RST} ${BLD}$(printf '$%.2f' "$session_cost")${RST}"
fi
[ -n "$s" ] && segs+=("$s")

# --- 3. cache warm/cold timer ---
# precedence: CLAUDE_CACHE_TTL > TTL seen in transcript > 1h
ttl="${CACHE_TTL:-${seen_ttl:-3600}}"
case "$ttl" in ''|*[!0-9]*) ttl=3600 ;; esac
if [ "$ttl" -ge 3600 ]; then ttl_label="$(( ttl / 3600 ))h"; else ttl_label="$(( ttl / 60 ))m"; fi
if [ -n "$last_ts" ] && last="$(date -d "$last_ts" +%s)" && [ -n "$last" ]; then
    left=$(( last + ttl - $(date +%s) ))
    if [ "$left" -gt 0 ]; then
        segs+=("${GRN}warm $(dur "$left") left${RST} ${DIM}(${ttl_label} ttl)${RST}")
    else
        segs+=("${RED}cold $(dur $(( -left ))) ago${RST} ${DIM}(${ttl_label} ttl)${RST}")
    fi
fi

for s in "${segs[@]}"; do printf ' %s│%s %s' "$DIM" "$RST" "$s"; done
printf '\n'
exit 0
