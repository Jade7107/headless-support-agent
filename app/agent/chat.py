from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agent.graph import support_agent
from langchain_core.messages import HumanMessage

router = APIRouter(tags=["Autonomous Support"])

class ChatRequest(BaseModel):
    thread_id: str  
    message: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        inputs = {"messages": [HumanMessage(content=request.message)]}
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # MAGIC UPGRADE: We 'await' the 'ainvoke' method so FastAPI can handle other users while the LLM thinks
        result = await support_agent.ainvoke(inputs, config=config)
        
        final_message = result["messages"][-1].content
        return {"status": "success", "response": final_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))