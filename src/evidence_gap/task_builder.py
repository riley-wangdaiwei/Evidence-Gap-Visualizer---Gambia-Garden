from .provenance import stable_id,now_iso
def build_task(title, description, priority="unassigned"):
    return {"id":stable_id("task",title,description),"title":title,"description":description,"priority":priority,"status":"draft","created_at":now_iso()}
def export_markdown(task): return f"# {task['title']}\n\nStatus: {task['status']}\nPriority: {task['priority']}\n\n{task['description']}\n"
