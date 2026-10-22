import plotly.graph_objects as go
BACKGROUND="#0B1016"
LAND="#17222C"
WATER="#0A1119"
VECTOR="#E8EEF2"
PALETTE={"low":"#4B918C","medium":"#B58B48","high":"#A34D42","unknown":"#454B50"}
def matrix(labels_x,labels_y,z,title,colorscale=None):
    fig=go.Figure(go.Heatmap(x=labels_x,y=labels_y,z=z,colorscale=colorscale or [[0,PALETTE["low"]],[.5,PALETTE["medium"]],[1,PALETTE["high"]]],hoverongaps=False,colorbar={"title":"Defined problem"}))
    fig.update_layout(title=title,paper_bgcolor=BACKGROUND,plot_bgcolor=BACKGROUND,font={"color":VECTOR},margin={"l":20,"r":20,"t":45,"b":20},height=560)
    fig.update_xaxes(showgrid=True,gridcolor="#26333D"); fig.update_yaxes(showgrid=True,gridcolor="#26333D")
    return fig

def empty_matrix(title,x_title,y_title,message):
    fig=go.Figure()
    fig.update_layout(title=title,paper_bgcolor=BACKGROUND,plot_bgcolor=BACKGROUND,font={"color":VECTOR},margin={"l":20,"r":20,"t":45,"b":20},height=560,xaxis_title=x_title,yaxis_title=y_title)
    fig.add_annotation(text=message,x=.5,y=.5,xref="paper",yref="paper",showarrow=False,font={"color":PALETTE["unknown"]})
    return fig
