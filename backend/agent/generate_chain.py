from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.schemas.chain import SearchResult


def create_recommendation_chain(llm: BaseChatModel):
    """
    Creates a generate chain for answering code-related questions.

    Args:
        llm (LLM): The language model to use for generating responses.

    Returns:
        A callable function that takes a context and a question as input and returns a string response.
    """
    system_prompt = """You are a product recommendation assistant that uses both user requirements and community discussions to identify and recommend products. You have just received several Reddit comment chunks discussing various products. Your job is to:

- Analyze the user's initial query and the retrieved Reddit documents to identify relevant products, brands, or categories that match the user's needs.
- Extract any product or brand mentions that are directly relevant to the user's criteria from the retrieved documents.

Important details:
- Focus only on product mentions that align with the user’s stated needs and is positive in nature.
- If multiple products are mentioned, consider all that align with the user’s criteria.
- Do not limit or prioritize based on price or budget unless the user explicitly requests it. Include products from all price ranges.

Format the generated response in JSON format by wrapping the output in `json` tags\n{format_instructions}"""

    users_query="""User’s query:
"{prompt}"

Below are the top Reddit comment chunks returned from a similarity search:
{resources}

Using the above Reddit content and the user query, please identify the products and brands that fit the user’s needs without filtering by budget."""


    # generate_prompt = PromptTemplate(template=system_prompt, input_variables=["prompt", "resources"])
    # generate_chain = generate_prompt | llm | StrOutputParser()

    parser = PydanticOutputParser(pydantic_object=SearchResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", users_query),
    ]).partial(format_instructions=parser.get_format_instructions())
    prompt.input_variables = ["prompt", "resources"]

    chain = prompt | llm | parser
    return chain


def create_e_commerce_chain(llm):
    ...

