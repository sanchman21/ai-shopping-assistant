import json
import logging

from langchain_community.tools import TavilySearchResults
from langchain_core.language_models import BaseChatModel
from langgraph.errors import create_error_message

from backend.agent.generate_chain import create_recommendation_chain
from backend.agent.graph import Steps, GraphState
from backend.agent.vector_store import Retriever
from backend.database.messages import create_message, MessageSenderEnum

logger = logging.getLogger(__name__)


class GraphNodes:
    def __init__(self, llm: BaseChatModel, retriever: Retriever, retrieval_grader, web_search_tool: TavilySearchResults):
        self.llm = llm
        self.retriever = retriever
        self.retrieval_grader = retrieval_grader
        self.web_search_tool = web_search_tool

        self.generate_chain = create_recommendation_chain(llm)

    def vector_store_retrieve(self, state):
        """
        Retrieve documents

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        print("---RETRIEVE---")
        prompt = state["prompt"]
        namespace = state["category"]

        # Retrieval
        documents = self.retriever.sim_search(prompt, namespace)
        state["resources"] = documents
        state["steps"] = [Steps.VECTOR_STORE_RETRIEVAL.value]

        return state

    def generate(self, state):
        """
        Generate answer

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation, that contains LLM generation
        """
        print("---GENERATE---")
        prompt = state["prompt"]
        # TODO: Handle Tavily web results by converting to Document
        resources = [r.page_content if hasattr(r, "page_content") else r for r in state["resources"]]

        # RAG generation
        generation = self.generate_chain.invoke({"resources": '\n'.join(f"{index + 1}. {item}" for index, item in enumerate(resources)), "prompt": prompt})


        tools_used = ["vector_search"]
        if state.get("perform_web_search", False):
            tools_used.append("web_search")

        create_message(content=prompt, chat_session_id=state["chat_session_id"], references=[], sender=MessageSenderEnum.USER,
                       tools_used=tools_used)
        create_message(content=json.dumps(generation.model_dump(mode="json")), chat_session_id=state["chat_session_id"], references=[r for r in resources],
                       sender=MessageSenderEnum.SYSTEM, tools_used=tools_used)

        state["generation"] = generation
        state["steps"].append(Steps.LLM_GENERATION.value)
        return state

    def _base_grade_documents(self, state: GraphState, previous_state: str):
        prompt = state["prompt"]
        resources = state["resources"]

        filtered_resources = []
        next_search = False

        for resource in resources:
            score = self.retrieval_grader.invoke({
                "prompt": prompt, "resources": resource
            })
            # print(f"{resource} || {score}")
            if score["score"].lower() == "yes":
                filtered_resources.append(resource)
            else:
                next_search = True
                continue

        if next_search:
            match previous_state:
                case "vector_store":
                    state["perform_web_search"] = True
                    state["steps"].append(Steps.VECTOR_STORE_EVALUATION.value)
        state["resources"] = filtered_resources

        return state

    def grade_vector_store_documents(self, state: GraphState):
        print("---GRADE VECTOR STORE DOCUMENTS---")
        return self._base_grade_documents(state, "vector_store")

    def web_search(self, state: GraphState):
        print("---WEB SEARCH - TAVILY---")

        prompt = state["prompt"]
        web_results = self.web_search_tool.invoke({"query": prompt})
        state["resources"] = [
           result["content"] for result in web_results
        ]
        state["steps"].append(Steps.WEB_SEARCH_RETRIEVAL.value)

        print(state["resources"])
        return state

    def transform_query(self, state):
        """
        Transform the query to produce a better question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates question key with a re-phrased question
        """
        print("---TRANSFORM QUERY---")
        question = state["input"]
        documents = state["documents"]

        # Re-write question
        better_question = self.question_rewriter.invoke({"input": question})
        return {"documents": documents, "input": better_question}
