import google.generativeai as genai
import dotenv
import re
import os
from .codeact_prompt import codeact_prompt
from .search_tool import OpenDeepSearchTool
from google import genai
from google.genai import types
from typing import Dict, List, Tuple, Any, Optional, Mapping
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils import io
from dataclasses import dataclass
dotenv.load_dotenv()

def final_answer(text: str) -> str:
    print(f"final answer: {text}")

tools={
    "final_answer": final_answer,
    "search_tool": OpenDeepSearchTool(
        serper_api_key=os.getenv('SERPER_API_KEY'),
        top_k=5,
        temperature=0.3
    )
}

class PythonREPL:
    def __init__(self, code: str, user_namespace: Mapping[str, Any]):
        self.code = code
        self.user_namespace = user_namespace
        self.shell = InteractiveShell.instance(
            user_ns=dict(self.user_namespace),
            colors="NoColor",
        )
    def reset(self) -> None:
        self.shell.clear_instance()
    def execute(self) -> str:
        try:
            with io.capture_output() as captured:
                _ = self.shell.run_cell(
                    self.code,
                    silent= True,
                    store_history=False,
                )
            output = captured.stdout
            if output == "":
                output = "[Executed Successfully with No Output]"
            return output
        except Exception as e:
            return str(e)


class CodeActAgent:
    def __init__(self, model_name: str = "gemini-2.0-flash", tools: Mapping[str, Any] = tools, verbose: bool = True):
        self.model_name = model_name
        self.model = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.system_prompt = codeact_prompt
        self.tools = tools
        self.verbose = verbose
    
    def _parse_response(self, response: str) -> Dict[str, Optional[str]]:
        thought_match = re.search(r'Thought:\s*(.*?)(?=Code:|Observation:|Final Answer:|$)', response, re.DOTALL)
        code_match = re.search(r'Code:\s*```(?:python)?\s*(.*?)```', response, re.DOTALL)
        observation_match = re.search(r'Observation:\s*(.*?)(?=Thought:|Code:|Final Answer:|$)', response, re.DOTALL)
        final_answer_match = re.search(r'Final Answer:\s*(.*?)$', response, re.DOTALL)
        
        result = {
            'thought': thought_match.group(1).strip() if thought_match else None,
            'code': code_match.group(1).strip() if code_match else None,
            'observation': observation_match.group(1).strip() if observation_match else None,
            'final_answer': final_answer_match.group(1).strip() if final_answer_match else None
        }
        
        if result['code'] and 'final_answer(' in result['code']:
            result['is_final'] = True
        else:
            result['is_final'] = False
            
        return result
    
    def _format_intermediate_steps(self, intermediate_steps: List[Tuple[str, str, str]]) -> str:
        formatted_steps = []
        for i, (thought, code, observation) in enumerate(intermediate_steps, 1):
            step = f"Step {i}:\n"
            if thought:
                step += f"Thought: {thought}\n"
            if code:
                step += f"Code:\n```python\n{code}\n```\n"
            if observation:
                step += f"Observation: {observation}\n"
            formatted_steps.append(step)
        return "\n".join(formatted_steps)
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        try:
            repl = PythonREPL(code, self.tools)
            output = repl.execute()
            return {
                'success': True,
                'output': output,
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'output': None,
                'error': str(e)
            }
    
    def _print_step(self, iteration: int, thought: str = "", code: str = "", observation: str = "", is_final: bool = False):
        if not self.verbose:
            return
            
        print(f"\n{'='*50}")
        print(f"ITERATION {iteration + 1}")
        print(f"{'='*50}")
        
        if thought:
            print(f"💭 THOUGHT:")
            print(f"   {thought}")
            print()
        
        if code:
            status = "🏁 FINAL CODE:" if is_final else "💻 CODE:"
            print(status)
            print(f"```python")
            print(code)
            print(f"```")
            print()
        
        if observation:
            print(f"👁️  OBSERVATION:")
            print(f"   {observation}")
            print()
    
    def run(self, user_question: str, max_iterations: int = 5) -> str:
        if self.verbose:
            print(f"\n🚀 Starting CodeAct Agent")
            print(f"📝 Question: {user_question}")
            print(f"🔄 Max iterations: {max_iterations}")
        
        intermediate_steps = []
        current_prompt = f"{self.system_prompt}\n\nQuestion: {user_question}\n\nPlease start by thinking about this step by step."
        
        for iteration in range(max_iterations):
            try:
                if self.verbose:
                    print(f"\n🔄 Generating response for iteration {iteration + 1}...")
                
                response = self.model.models.generate_content(
                    model=self.model_name,
                    contents=[{
                        'role': 'user',
                        'parts': [{'text': current_prompt}]
                    }]
                )
                
                response_text = response.candidates[0].content.parts[0].text
                parsed = self._parse_response(response_text)
                
                thought = parsed.get('thought', '')
                code = parsed.get('code', '')
                
               
                if parsed.get('final_answer'):
                    if self.verbose:
                        print(f"\n🎯 FINAL ANSWER RECEIVED:")
                        print(f"   {parsed['final_answer']}")
                    return parsed['final_answer']
                
              
                if code and not parsed.get('is_final', False):
                   
                    self._print_step(iteration, thought, code, "", False)
                    
                    if self.verbose:
                        print("⚡ Executing code...")
                    
                    execution_result = self.execute_code(code)
                    
                    if execution_result['success']:
                        observation = execution_result['output']
                    else:
                        observation = f"Error: {execution_result['error']}"
                    
                
                    if self.verbose:
                        print(f"👁️  OBSERVATION:")
                        print(f"   {observation}")
                    
            
                    intermediate_steps.append((thought, code, observation))
                    
                   
                    history = self._format_intermediate_steps(intermediate_steps)
                    current_prompt = f"{self.system_prompt}\n\nQuestion: {user_question}\n\n{history}\n\nWhat should I do next?"
                
                elif code and parsed.get('is_final', False):
              
                    self._print_step(iteration, thought, code, "", True)
                    
                    if self.verbose:
                        print("🏁 Executing final code...")
                    
                    execution_result = self.execute_code(code)
                    if execution_result['success']:
                        if self.verbose:
                            print(f"✅ Final execution successful!")
                            print(f"🎯 RESULT: {execution_result['output']}")
                        return execution_result['output']
                    else:
                        error_msg = f"Error in final answer: {execution_result['error']}"
                        if self.verbose:
                            print(f"❌ Final execution failed: {error_msg}")
                        return error_msg
                
                else:
                    self._print_step(iteration, thought, "", "", False)
                    
                    if thought:
                        intermediate_steps.append((thought, '', ''))
                        history = self._format_intermediate_steps(intermediate_steps)
                        current_prompt = f"{self.system_prompt}\n\nQuestion: {user_question}\n\n{history}\n\nPlease provide code to execute or a final answer."
            
            except Exception as e:
                error_msg = f"Error during execution: {str(e)}"
                if self.verbose:
                    print(f"❌ {error_msg}")
                return error_msg
        
        if self.verbose:
            print(f"\n⚠️  Reached maximum iterations ({max_iterations}). Synthesizing final answer...")
        
        return self._synthesize_from_history(user_question, intermediate_steps, thought)
    
    def _synthesize_from_history(self, original_question: str, action_history: List[Tuple[str, str, str]], last_thought: str) -> str:
        history_summary = self._format_intermediate_steps(action_history)
        
        synthesis_prompt = f"""
        {self.system_prompt}
        
        Original Question: {original_question}
        
        Here's what I've tried so far:
        {history_summary}
        
        Last thought: {last_thought}
        
        Based on all the work above, please provide a final answer to the original question. 
        If you couldn't fully solve it, explain what you discovered and what the limitations were.
        
        Final Answer: [Your answer here]
        """
        
        try:
            if self.verbose:
                print("🔄 Generating synthesis response...")
            
            response = self.model.models.generate_content(
                model=self.model_name,
                contents=[{
                    'role': 'user',
                    'parts': [{'text': synthesis_prompt}]
                }]
            )
            
            response_text = response.candidates[0].content.parts[0].text
            parsed = self._parse_response(response_text)
            
            final_answer = parsed.get('final_answer', response_text)
            
            if self.verbose:
                print(f"📋 SYNTHESIZED ANSWER:")
                print(f"   {final_answer}")
            
            return final_answer
            
        except Exception as e:
            error_msg = f"Could not synthesize final answer due to error: {str(e)}. Based on the work done, here's a summary of findings: {history_summary}"
            if self.verbose:
                print(f"❌ Synthesis failed: {error_msg}")
            return error_msg


# if __name__ == "__main__":
    
    
#     agent = CodeActAgent(
#     system_prompt=codeact_prompt,
#     tools={
#         "final_answer": final_answer,
#         "search_tool": OpenDeepSearchTool(
#             serper_api_key=os.getenv('SERPER_API_KEY'),
#             top_k=5,
#             temperature=0.3
#         )
#     },
#     verbose=True 
#     )

#     question = "What is the current population of Vietnam, and how many cakes are needed if each person gets 2 cakes?"
#     result = agent.run(question)
#     print(f"\n🏆 FINAL RESULT: {result}")