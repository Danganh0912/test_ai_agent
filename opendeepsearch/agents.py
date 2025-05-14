import sys
import os
current_dir = os.path.dirname(__file__)  
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)
from opendeepsearch.prompt import react_system_prompt
from opendeepsearch.calculate_tools import CalculateTool
from opendeepsearch.search_tool import OpenDeepSearchTool
from langchain.schema import AgentAction, AgentFinish
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from typing import Dict, List, Optional, Tuple, Union
import re

import dotenv

api_key = os.getenv('SERPER_API_KEY')
dotenv.load_dotenv()


class ReActAgent:
    def __init__(self, model_name="qwen2.5:14b-instruct-q8_0", temperature=0.3):
        self.llm = ChatOllama(model=model_name, temperature=temperature)
        self.system_prompt = react_system_prompt
            
    def _parse_response(self, response: str) -> Tuple[str, Optional[AgentAction], Optional[AgentFinish]]:
        thought_match = re.search(r"Thought:(.*?)(?:Action:|$)", response, re.DOTALL)
        action_match = re.search(r"Action:(.*?)(?:Action Input:|$)", response, re.DOTALL)
        action_input_match = re.search(r"Action Input:(.*?)(?:Observation:|$)", response, re.DOTALL)
        
        thought = thought_match.group(1).strip() if thought_match else ""
        action = action_match.group(1).strip() if action_match else None
        action_input = action_input_match.group(1).strip() if action_input_match else None
        
        print(f"DEBUG - Parsed components: Thought found: {bool(thought)}, Action: '{action}', Action Input exists: {bool(action_input)}")
        
        if action == "Finish":
            return thought, None, AgentFinish(return_values={"output": action_input}, log=thought)
        elif action:
            return thought, AgentAction(tool=action, tool_input=action_input, log=thought), None
        else:
            if thought and "final answer" in thought.lower():
                print("DEBUG - Detected final answer intent in thought")
                return thought, None, AgentFinish(return_values={"output": thought}, log=thought)
            return thought, None, None
            
    def _format_intermediate_steps(self, intermediate_steps: List[Tuple[AgentAction, str]]) -> str:
        formatted_steps = ""
        for action, observation in intermediate_steps:
            formatted_steps += f"Action: {action.tool}\n"
            formatted_steps += f"Action Input: {action.tool_input}\n"
            formatted_steps += f"Observation: {observation}\n"
            formatted_steps += "Thought: "
        return formatted_steps
    
    def execute_tool(self, tool_name: str, tool_input: str, context: str) -> str:
        tool_name = tool_name.strip()
        if tool_name == "calculate":
            return CalculateTool.execute(tool_input)
        elif tool_name == "web_search":
            return OpenDeepSearchTool(serper_api_key=api_key).run(tool_input)
        else:
            return f"Unknown tool: {tool_name}"
    
    def run(self, user_question: str, context: str, max_iterations: int = 5) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Context: {context}"},
            {"role": "user",   "content": (
                f"Answer the question using ReAct.\n"
                f"Question: {user_question}\n"
                f"Begin with a Thought:"
            )}
        ]

        action_history = []

        for iteration in range(1, max_iterations + 1):
            response = self.llm.invoke(messages)
            content = response.content.strip()
            thought, action, final = self._parse_response(content)

            print(f"[Iter {iteration}] Thought: {thought}")

            if final:
                answer = final.return_values.get("output", "")
                print(f"Final answer obtained in {iteration} iterations.")
                return answer

            if not action:
                print(f"No action parsed at iteration {iteration}. Stopping.")
                break

            print(f"[Iter {iteration}] Executing tool: {action.tool}")
            print(f"Action Input: {action.tool_input}")
            observation = self.execute_tool(action.tool, action.tool_input, context)
            print(f"Observation: {observation}")
            
            action_history.append((action.tool, action.tool_input, observation))

            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Observation: {observation}\nThought:"})

        print("Max iterations reached without a final answer.")
 
        if action_history:
            return self._synthesize_from_history(user_question, action_history, thought)
        return content
    
    def _synthesize_from_history(self, original_question: str,
                               action_history: List[Tuple[str, str, str]], 
                               last_thought: str) -> str:
        action_summary = "\n".join([
            f"- Used {action} tool with input '{tool_input}' and got: {observation}"
            for action, tool_input, observation in action_history
        ])
        
        prompt = f"""Based on the original question and the information gathered from tools,
        synthesize a comprehensive answer.
        Original Question: {original_question}
        Information Gathered:
        {action_summary}
        
        Last Thought: {last_thought}
        
        What is the answer to the original question based on this information?"""
        
        messages = [
            {"role": "system", "content": "You are an expert at synthesizing information to answer questions accurately."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm.invoke(messages)
            final_answer = response.content.strip()
            return final_answer
        except Exception as e:
            print(f"Error synthesizing from history: {e}")
            return f"Based on the tools used, I can determine: {action_summary}"


def get_ollama_response(user_question: str, context: str) -> str:
    try:
        react_agent = ReActAgent(model_name="qwen2.5:14b-instruct-q8_0", temperature=0.3)
        response = react_agent.run(user_question, context)
        return response
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_ollama_response: {e}\n{error_details}")
        return f"Error occurred while processing your question: {str(e)}"


if __name__ == "__main__":
    question = "calculate for me the product and quotient of 8 and 2"
    context = "The user wants to perform a calculation and search for information."
    response = get_ollama_response(question, context)
    print("\nFinal Response:")
    print(response)