"""
World map: the same Plotly figure works as an HTML snapshot and inline in notebooks.
"""

from pathlib import Path

import plotly.graph_objects as go

from ml_based_strategies.viz.schema import Style
from ml_based_strategies.world.graph import World


def world_figure(world: World, style: Style) -> go.Figure:
    fig = go.Figure()
    locs_dict = world.locations_dict

    # e(x/y) - edges: one line trace (None breaks segments) 
    # m(x/y) - midpoint cost labels carrying the hover.
    ex_lst, ey_lst, mx_lst, my_lst, mcost_lst, mtext_lst = [], [], [], [], [], []
    
    # adj - adjacency, ngbrs - neighbors, pt - point, la/lb - location a/b
    for org_pt, ngbrs_dict in world.adjacency_dict.items():
        for trg_pt, cost in ngbrs_dict.items():
            if org_pt < trg_pt:
                la, lb = locs_dict[org_pt], locs_dict[trg_pt]

                # edges 
                ex_lst += [la.x, lb.x, None]
                ey_lst += [la.y, lb.y, None]

                # midpoints
                mx_lst.append((la.x + lb.x) / 2)
                my_lst.append((la.y + lb.y) / 2)

                # hover text
                mcost_lst.append(str(cost))
                mtext_lst.append(f"{la.name} ↔ {lb.name}<br>cost: {cost}")

    fig.add_trace(go.Scatter(x=ex_lst, y=ey_lst, mode="lines", line={"color": "#bbbbbb", "width": 2}, hoverinfo="skip"))
    fig.add_trace(
        go.Scatter(
            x=mx_lst,
            y=my_lst,
            mode="markers+text",
            marker={"opacity": 0},
            text=mcost_lst,
            textfont={"color": "#666666", "size": 11},
            hovertext=mtext_lst,
            hoverinfo="text",
        )
    )

    # Nodes: one trace per owner so the legend doubles as a faction key.
    owner_ids_lst = [*world.factions_dict, None]
    for owner_id in owner_ids_lst:
        owner_loc_lst = [loc for loc in locs_dict.values() if loc.owner == owner_id]
        if not owner_loc_lst:
            continue
        faction = world.factions_dict.get(owner_id) if owner_id else None
        fig.add_trace(
            go.Scatter(
                x=[loc.x for loc in owner_loc_lst],
                y=[loc.y for loc in owner_loc_lst],
                mode="markers+text",
                name=faction.name if faction else "Unclaimed",
                text=[loc.name for loc in owner_loc_lst],
                textposition="top center",
                marker={
                    "size": 18,
                    "color": faction.color if faction else style.neutral,
                    "symbol": ["star" if loc.protected else "circle" for loc in owner_loc_lst],
                    "line": {"width": 1, "color": "#222"},
                },
                hovertext=[
                    f"<b>{loc.name}</b><br>kind: {loc.kind}<br>owner: {faction.name if faction else '—'}"
                    + ("<br>protected" if loc.protected else "")
                    for loc in owner_loc_lst
                ],
                hoverinfo="text",
            )
        )

    fig.update_layout(
        title="Simulation grounds",
        showlegend=True,
        template="plotly_white",
        xaxis={"visible": True, "showgrid": True},
        yaxis={"visible": True, "showgrid": True, "scaleanchor": "x"},
    )

    # Hide the two edge helper traces from the legend.
    fig.data[0].showlegend = fig.data[1].showlegend = False
    return fig


def save_snapshot(world: World, style: Style, path: str | Path) -> Path:
    # path resolution
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # CDN to lighten the HTML snapshot (be aware of offline use - change for JS if needed).
    world_figure(world, style).write_html(path, include_plotlyjs="cdn")
    return path
