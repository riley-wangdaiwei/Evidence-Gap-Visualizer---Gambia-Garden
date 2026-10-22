import plotly.graph_objects as go
BACKGROUND="#0B1016"
LAND="#17222C"
WATER="#0A1119"
VECTOR="#E8EEF2"
PALETTE={"low":"#4B918C","medium":"#B58B48","high":"#A34D42","unknown":"#454B50"}
STATE_COLORS={"NOT_SEARCHED_OR_UNKNOWN":"#454B50","SEARCH_INCOMPLETE":"#65615A","SEARCHED_NO_DIRECT_EVIDENCE_FOUND":"#A34D42","INDIRECT_OR_NOT_COMPARABLE_EVIDENCE":"#B58B48","DIRECT_EVIDENCE_FOUND":"#4B918C","MULTIPLE_INDEPENDENT_DIRECT_SOURCES":"#287B72","RESTRICTED_ACCESS":"#8B6445","OUTDATED_OR_TEMPORALLY_MISMATCHED":"#A34D42","INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION":"#65615A"}
RELATION_COLORS={"DIRECT_MATCH":"#287B72","HARMONIZABLE":"#4B918C","PROXY":"#B58B48","CONCEPTUALLY_RELATED":"#B87942","INCOMPATIBLE":"#A34D42","UNKNOWN_REQUIRES_REVIEW":"#454B50"}
def matrix(labels_x,labels_y,z,title,colorscale=None,*,text=None,hovertext=None,zmax=5):
    if colorscale is None:
        colorscale=[[0,PALETTE["unknown"]],[1,PALETTE["unknown"]]]
    fig=go.Figure(go.Heatmap(x=labels_x,y=labels_y,z=z,colorscale=colorscale,zmin=0,zmax=zmax,showscale=False,hoverongaps=False,text=text,texttemplate="%{text}" if text else None,hovertext=hovertext,hovertemplate="%{hovertext}<extra></extra>" if hovertext else None))
    fig.update_layout(title=title,paper_bgcolor=BACKGROUND,plot_bgcolor=WATER,font={"color":VECTOR},margin={"l":20,"r":20,"t":45,"b":20},height=560)
    fig.update_xaxes(showgrid=True,gridcolor="#26333D",side="bottom"); fig.update_yaxes(showgrid=True,gridcolor="#26333D",autorange="reversed")
    return fig

def categorical_scale(labels, palette):
    n=max(len(labels),1)
    colors=[]
    for i,label in enumerate(labels):
        color=palette.get(label,PALETTE["unknown"])
        denom=max(n-1,1)
        lo=0 if i==0 else (i-.5)/denom
        hi=1 if i==n-1 else (i+.5)/denom
        colors.extend([[lo,color],[hi,color]])
    return colors

def add_cell_layers(fig, *, x_index, y_index, vector=False, source_count=0, derivation_status="RULE_DERIVED", friction=False):
    if vector:
        status=derivation_status if derivation_status in ("RULE_DERIVED","HUMAN_REVIEWED") else "HUMAN_REVIEWED"
        fig.add_annotation(x=x_index,y=y_index+0.24,ax=x_index,ay=y_index-0.24,xref="x",yref="y",axref="x",ayref="y",showarrow=True,arrowhead=3,arrowsize=1,arrowwidth=max(1,min(5,1+source_count)),arrowcolor=VECTOR,text="R" if status=="RULE_DERIVED" else "H",hovertext=f"{status}; independent sources: {source_count}")

def add_friction_markers(fig, points):
    if not points:return
    fig.add_trace(go.Scatter(x=[p["x"] for p in points],y=[p["y"] for p in points],
        customdata=[[p["id"],p["type"],p["description"]] for p in points],
        mode="markers",marker={"symbol":"x-thin","size":14,"color":PALETTE["medium"]},
        name="Typed barrier",hovertemplate="%{customdata[1]}<br>%{customdata[2]}<extra>Click for evidence and verification</extra>"))

def empty_matrix(title,x_title,y_title,message):
    fig=go.Figure()
    fig.update_layout(title=title,paper_bgcolor=BACKGROUND,plot_bgcolor=WATER,font={"color":VECTOR},margin={"l":20,"r":20,"t":45,"b":20},height=560,xaxis_title=x_title,yaxis_title=y_title)
    fig.add_annotation(text=message,x=.5,y=.5,xref="paper",yref="paper",showarrow=False,font={"color":PALETTE["unknown"]})
    return fig
