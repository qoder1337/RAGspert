import json
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from src.database import sessionmanager_pgvector, DatabaseSessionManager
from src.database.models.agent_sitepage import SitePage
from sqlalchemy.future import select
from sqlalchemy import text
from src.utils.text_embedder import get_embedding_single
from src.utils.llm.gemini_cl import gemini_model


@dataclass
class DocumentationDeps:
    sessionmanager_pgvector: DatabaseSessionManager
    source_filter: str


def make_system_prompt(
    library_name: str = "Python library", language: str = "en"
) -> str:
    """Generate system prompt for documentation RAG assistant.

    Args:
        library_name: Name of the library/framework being documented
        language: Output language ('de' for German, 'en' for English)
    """
    lang_name = "German" if language == "de" else "English"
    no_data_msg = (
        "Keine Daten in der Dokumentation gefunden."
        if language == "de"
        else "No data found in documentation."
    )

    return f"""You are an expert assistant for {library_name} documentation.

Your role:
- Help users understand and work with {library_name} using the official documentation
- Answer ONLY questions related to {library_name} - politely decline other topics
- Always respond in {lang_name}

Search strategy:
1. Use RAG (vector similarity search) first to find relevant documentation
2. Check multiple documentation sections if the first result is insufficient
3. Retrieve specific pages when needed for detailed information

Response guidelines:
- Provide code examples when helpful (keep them in their original language)
- Cite specific documentation sections when possible
- Be direct and actionable - don't ask for permission before using tools
- If the answer is not in the documentation, be honest and say: "{no_data_msg}"

Critical rules:
- ONLY answer when you have found the information in the documentation database
- Never make up information or rely on general knowledge outside the provided context
- If uncertain or data is missing, always respond with: "{no_data_msg}"
"""


class RAGAgent:
    def __init__(self, library_name: str = "Python library", language: str = "en"):
        self.system_prompt = make_system_prompt(library_name, language)
        self.agent = Agent(
            model=gemini_model,
            system_prompt=self.system_prompt,
            deps_type=DocumentationDeps,
            retries=2,
        )

        # Register tools
        self.agent.tool(retrieve_relevant_documentation)
        self.agent.tool(list_documentation_pages)
        self.agent.tool(get_page_content)

    async def run(self, query: str, source_filter: str):
        """
        Run agent with specific source filter.

        Args:
            query: User question
            source_filter: Documentation source (i.e. "Pydantic AI", "FastAPI")
        """
        agent_deps = DocumentationDeps(
            sessionmanager_pgvector=sessionmanager_pgvector,
            source_filter=source_filter,
        )

        result = await self.agent.run(query, deps=agent_deps)
        return result.output


# The tools need to be defined before they are registered.
# Let's define a placeholder for the agent that the decorators can use.
# This will be replaced inside the RAGAgent class.
documentation_expert = Agent()


@documentation_expert.tool
async def retrieve_relevant_documentation(
    ctx: RunContext[DocumentationDeps] = None, user_query: str = None
) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.

    Args:
        ctx: The context including the pbvector/db client and gemini/llm client
        user_query: The user's question or query

    Returns:
        A formatted string containing the top 5 most relevant documentation chunks
    """
    try:
        query_embedding = await get_embedding_single(user_query)

        clean_source = ctx.deps.source_filter.strip('"')

        async with ctx.deps.sessionmanager_pgvector.session() as session:
            result = await session.execute(
                text("""
                    SELECT *
                    FROM match_site_pages(
                        CAST(:query_embedding AS vector),
                        :match_count,
                        :filter
                    )
                """),
                {
                    "query_embedding": json.dumps(query_embedding),
                    "match_count": 5,
                    "filter": json.dumps({"source": clean_source}),
                },
            )

            # Use .mappings() to return rows as dictionaries
            rows = result.mappings().all()  # This will give you a list of dictionaries

        if not rows:
            print("No relevant documentation found.")
            return "No relevant documentation found."

        print("================\nretrieve_relevant_documentation ROWS: ", rows)
        # Format the results
        formatted_chunks = []
        for row in rows:
            chunk_text = f"""
# {row["title"]}

{row["content"]}
"""
            formatted_chunks.append(chunk_text)

        # Join all chunks with a separator
        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        print(f"Error retrieving documentation: {e}")
        return f"Error retrieving documentation: {str(e)}"


@documentation_expert.tool
async def list_documentation_pages(
    ctx: RunContext[DocumentationDeps] = None,
) -> list[str]:
    """
    Retrieve a list of all available documentation pages of the desired library.

    Returns:
        List[str]: List of unique URLs for all documentation pages
    """
    try:
        clean_source = ctx.deps.source_filter.strip('"')

        async with ctx.deps.sessionmanager_pgvector.session() as session:
            stmt = select(SitePage.url).where(text("meta_details->>'source' = :source"))

            result = await session.execute(stmt, {"source": clean_source})

            urls = sorted(set(row[0] for row in result.fetchall()))

        return urls

    except Exception as e:
        print(f"Error retrieving documentation pages: {e}")
        return []


@documentation_expert.tool
async def get_page_content(
    ctx: RunContext[DocumentationDeps] = None, url: str = None
) -> str:
    """
    Retrieve the full content of a specific documentation page by combining all its chunks.

    Args:
        ctx: The context including the db client
        url: The URL of the page to retrieve

    Returns:
        str: The complete page content with all chunks combined in order
    """
    try:
        clean_source = ctx.deps.source_filter.strip('"')

        async with ctx.deps.sessionmanager_pgvector.session() as session:
            stmt = (
                select(
                    SitePage.title,
                    SitePage.content,
                    SitePage.chunk_number,
                )
                .where(SitePage.url == url)
                .where(text("meta_details->>'source' = :source"))
                .order_by(SitePage.chunk_number)
            )

            result = await session.execute(stmt, {"source": clean_source})
            rows = result.fetchall()

            print(f"===========\nget_page_content {rows=}")

        if not rows:
            return f"No content found for URL: {url} in {clean_source}"

        page_title = rows[0][0].split(" - ")[0]
        formatted_content = [f"# {page_title}\n"]

        for row in rows:
            formatted_content.append(row[1])

        output = "\n\n".join(formatted_content)

        return output

    except Exception as e:
        return f"Error retrieving page content: {str(e)}"
