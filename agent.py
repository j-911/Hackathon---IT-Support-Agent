import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate

# Local imports
from ticket import Ticket
from utils import colorize

class ITHelpdeskAgent:
    """An agent that handles IT support queries and ticket management."""
    def __init__(self):
        self.tickets = {}
        self.next_ticket_id = 1
        self.llm = None
        self.qa_chain = None
        self.history = []
        self._initialize_agent()

    def _initialize_agent(self):
        """Loads environment variables, models, and sets up the RAG pipeline."""
        load_dotenv()
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Error: GOOGLE_API_KEY environment variable not set.")

        self.llm = GoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.2)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        policies_path = "./it_policies"
        faiss_index_path = "faiss_index_it_policies"

        if not os.path.exists(policies_path):
            os.makedirs(policies_path)
            print(colorize(f"Created directory '{policies_path}'. Please add your IT policy/guide files (.md or .txt) there.", "\033[33m"))

        vector_store = self._load_or_create_vector_store(faiss_index_path, policies_path, embeddings)
        if not vector_store:
            print(colorize("Could not initialize vector store. Exiting.", "\033[31m"))
            exit()

        prompt_template = """
        You are an advanced AI IT Helpdesk Agent. Your primary function is to assist employees by consulting a knowledge base of official IT policies and troubleshooting guides. You must adhere to the following rules:

        1.  **Consult the Context First:** Use the provided context below to answer the user's question. The context contains official IT documentation.
        2.  **Do Not Invent Answers:** If the answer is not in the context, state that you cannot find the information in the knowledge base and recommend creating a ticket.
        3.  **Provide Structured Answers:** For "how-to" questions, your answer MUST include these three parts:
            a. A clear, step-by-step checklist for the user to follow.
            b. A status statement: explicitly state if the action is "Allowed," "Denied," or "Requires Approval" based on the policy.
            c. A citation: reference the policy that justifies your response (e.g., "This is based on Policy ID: VPN-001").
        4.  **Handle Ambiguity:** If policies conflict or the user's query is missing details (like their role or device), explain which rules you are considering, why there is ambiguity, and what specific information you need to provide a definitive answer.

        Context:
        {context}

        Question:
        {question}

        Helpful Answer:
        """
        QA_CHAIN_PROMPT = PromptTemplate.from_template(prompt_template)

        self.qa_chain = RetrievalQA.from_chain_type(
            self.llm,
            retriever=vector_store.as_retriever(),
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )
        print(colorize("IT Support Agent is ready. 🚀", "\033[36m"))

    def _load_or_create_vector_store(self, index_path, data_path, embeddings):
        """Loads a FAISS vector store from disk or creates it if it doesn't exist."""
        if os.path.exists(index_path):
            print(colorize(f"Loading existing vector store from '{index_path}'...", "\033[32m"))
            try:
                return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(colorize(f"Error loading vector store: {e}. Rebuilding...", "\031m"))

        print(colorize("Creating new vector store from IT policies...", "\033[32m"))
        loader = DirectoryLoader(
            data_path, glob="**/*.md", loader_cls=TextLoader,
            show_progress=True, use_multithreading=True
        )
        documents = loader.load()

        if not documents:
            print(colorize(f"Warning: No documents found in '{data_path}'. The agent will not be able to answer policy questions.", "\033[33m"))
            return None

        print(colorize(f"Loaded {len(documents)} policy documents. Creating embeddings...", "\033[32m"))
        vector_store = FAISS.from_documents(documents, embeddings)
        vector_store.save_local(index_path)
        print(colorize(f"Vector store created and saved to '{index_path}'.", "\033[32m"))
        return vector_store

    def create_ticket(self, description):
        """Creates a new IT support ticket and returns a confirmation string."""
        ticket_id = self.next_ticket_id
        new_ticket = Ticket(ticket_id, description)
        self.tickets[ticket_id] = new_ticket
        self.next_ticket_id += 1
        
        update_msg = new_ticket.update_status("In Progress", "Assigned to IT workflow.")
        
        return (
            f"✅ Ticket #{ticket_id} created successfully.\n"
            f"An IT staff member will be assigned to it shortly.\n"
            f"{update_msg}"
        )

    def get_guidance(self, question):
        """Answers a 'how-to' question using the RAG chain, including conversation history."""
        formatted_history = "\n".join(self.history)
        
        if formatted_history:
            input_text = (
                "Considering the following conversation history:\n"
                f"---\n{formatted_history}\n---\n\n"
                f"Now, please answer this question: {question}"
            )
        else:
            input_text = question

        try:
            result = self.qa_chain.invoke({"query": input_text})
            return result["result"]
        except Exception as e:
            return f"An error occurred while processing your request: {e}"

    def process_command(self, user_input):
        """
        Processes user input from any interface and returns a string response.
        This is the central logic hub for the agent.
        """
        if not user_input:
            return ""

        lower_input = user_input.lower()
        parts = user_input.split()

        if lower_input == 'exit':
            return "Thank you for using the IT Helpdesk. Goodbye!"
        elif lower_input == 'clear':
            self.history = []
            return "Conversation memory has been cleared."
        elif lower_input.startswith('status'):
            try:
                ticket_id = int(parts[1])
                ticket = self.tickets.get(ticket_id)
                return str(ticket) if ticket else f"Error: Ticket with ID {ticket_id} not found."
            except (IndexError, ValueError):
                return "Invalid command. Use 'status <ticket_id>'."
        elif lower_input.startswith('close'):
            try:
                ticket_id = int(parts[1])
                ticket = self.tickets.get(ticket_id)
                if not ticket:
                    return f"Error: Ticket with ID {ticket_id} not found."
                
                resolution_code = " ".join(parts[2:])
                if not resolution_code:
                    return "A resolution code is required. Use 'close ticket_id [resolution_text]'."

                msg1 = ticket.update_status("Resolved", f"Resolution code provided: {resolution_code}")
                msg2 = ticket.update_status("Closed", "Ticket lifecycle complete.")
                return f"{msg1}\n{msg2}"

            except (IndexError, ValueError):
                return "Invalid command. Use 'close <ticket_id> <resolution_text>'."
        elif 'how' in lower_input or 'what' in lower_input or '?' in lower_input:
            answer = self.get_guidance(user_input)
            
            self.history.append(f"User: {user_input}")
            self.history.append(f"Agent: {answer}")
            if len(self.history) > 10:
                self.history = self.history[-10:]
            
            return f"--- Knowledge Base Answer ---\n{answer}\n---------------------------"
        else:
            return self.create_ticket(user_input)

    def run(self):
        """Starts the main interaction loop for the Support agent in the terminal."""
        print(colorize("\n--- Welcome to the IT Support ---", "\033[35m"))
        print(colorize("You can: ", "\033[36m"))
        print(colorize("   - Describe a problem to create a ticket (e.g., 'My VPN is not working').", "\033[36m"))
        print(colorize("   - Ask a general question (e.g., 'How do I reset my password?').", "\033[36m"))
        print(colorize("   - Use 'status [id]' to check a ticket.", "\033[36m"))
        print(colorize("   - Use 'close [id]' to close a ticket with a resolution code.", "\033[36m"))
        print(colorize("   - Use 'clear' to reset the conversation memory.", "\033[36m"))
        print(colorize("   - Use 'exit' to quit.", "\033[36m"))

        while True:
            user_input = input(colorize("\n> ", "\033[33m")).strip()
            
            if user_input.lower() == 'exit':
                print(colorize("Thank you for using the IT Support. Goodbye!", "\033[35m"))
                break

            if user_input.lower().startswith('close'):
                parts = user_input.split()
                try:
                    ticket_id = int(parts[1])
                    if self.tickets.get(ticket_id):
                        resolution_code = input(colorize("Please provide a valid resolution code to close the ticket: ", "\033[33m"))
                        if resolution_code:
                            full_command = f"close {ticket_id} {resolution_code}"
                            response = self.process_command(full_command)
                            print(colorize(response, "\033[32m"))
                        else:
                            print(colorize("A resolution code is required to close the ticket.", "\033[31m"))
                    else:
                        print(colorize(f"Error: Ticket with ID {ticket_id} not found.", "\033[31m"))
                except (IndexError, ValueError):
                    print(colorize("Invalid command. Use 'close <ticket_id>'.", "\033[31m"))
            else:
                if 'how' in user_input.lower() or 'what' in user_input.lower() or '?' in user_input.lower():
                    print(colorize("Consulting the knowledge base (with memory)...", "\033[90m"))
                response = self.process_command(user_input)
                print(colorize(response, "\033[34m"))