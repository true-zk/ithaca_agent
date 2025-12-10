from ithaca.workflow.data_type import WorkFlowInput, MarketingInitInput
from ithaca.workflow.demo_workflow import DemoWorkFlow


def main():
    input = MarketingInitInput(
        product_name="",
        product_url="",
        product_picture_urls=[]
    )
    workflow_input = WorkFlowInput(
        marketing_init_input=input
    )

    workflow = DemoWorkFlow(workflow_input)