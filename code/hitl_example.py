from typing import Literal, Optional, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ApprovalState(TypedDict):
    action_details: str
    status: Optional[Literal["pending", "approved", "rejected"]]


def approval_node(state: ApprovalState) -> Command[Literal["proceed", "cancel"]]:
    decision = interrupt(
        {
            "question": "Approve this action?",
            "details": state["action_details"],
        }
    )
    return Command(goto="proceed" if decision else "cancel")


def proceed_node(state: ApprovalState):
    return {"status": "approved"}


def cancel_node(state: ApprovalState):
    return {"status": "rejected"}


builder = StateGraph(ApprovalState)
builder.add_node("approval", approval_node)
builder.add_node("proceed", proceed_node)
builder.add_node("cancel", cancel_node)
builder.add_edge(START, "approval")
builder.add_edge("proceed", END)
builder.add_edge("cancel", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "approval-123"}}

# === STEP 1: Run until interrupt ===
print("Starting workflow...")
stream = graph.stream_events(
    {"action_details": "Transfer $500", "status": "pending"},
    config=config,
    version="v3",
)

# Consume the stream to hit the interrupt
for _ in stream:
    pass

# === STEP 2: Check for interrupts and ASK THE USER ===
if stream.interrupts:
    interrupt_data = stream.interrupts[0].value
    print(f"\n{interrupt_data['question']}")
    print(f"Details: {interrupt_data['details']}")
    
    # ← THIS IS WHAT WAS MISSING - ACTUALLY GET USER INPUT
    while True:
        user_input = input("\nApprove? (yes/no): ").strip().lower()
        if user_input in ("yes", "y"):
            decision = True
            break
        elif user_input in ("no", "n"):
            decision = False
            break
        print("Please enter 'yes' or 'no'")
    
    # === STEP 3: Resume with USER'S decision ===
    print(f"\nResuming with: {'APPROVED' if decision else 'REJECTED'}")
    resumed = graph.stream_events(
        Command(resume=decision),  # Use the user's actual decision
        config=config,
        version="v3",
    )
    
    for _ in resumed:
        pass
    
    print(f"Final status: {resumed.output['status']}")
else:
    print("No interrupt occurred")