import sys
import warnings
import os
import subprocess
from datetime import datetime

# pyrefly: ignore [missing-import]
import litellm
litellm.drop_params = True

# pyrefly: ignore [missing-import]
from crewai import Crew
from engineering_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

requirements = """
A simple account management system for a trading simulation platform supporting multiple stock symbols.
The system should allow users to:
1. Create an account, deposit funds, and withdraw funds.
2. Record transactions for buying or selling shares of various stock symbols (e.g., AAPL, TSLA, GOOGL) and hold multiple different stocks in their portfolio simultaneously.
3. Calculate the total value of the user's portfolio (cash balance + current market value of all stock holdings) and the profit/loss compared to the initial deposit.
4. Report the complete stock holdings of the user at any point in time, displaying them as a detailed list or table.
5. Report the profit or loss of the user at any point in time.
6. List the complete transaction history over time.
7. Prevent the user from withdrawing funds that would leave them with a negative balance, buying more shares than they can afford, or selling shares they do not own.

The system has access to a function get_share_price(symbol) which returns the current price of a share, and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL.

Gradio UI Requirements:
- The UI must display a clear, dedicated status/notification text block at the bottom of the interface to output success alerts (e.g. 'Successfully deposited $100!') and error messages (e.g. 'Error: Insufficient funds!') when transactions occur.
- The UI must render a table or list showing all currently owned stocks (Ticker, Quantity, Current Price, and Total Value of the holding) on the Portfolio page.
"""
module_name = "accounts.py"
class_name = "Account"

def clean_output_files(directory="output"):
    """Scans output files and cleans any markdown formatting wrappers."""
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath) and (filename.endswith(".py") or filename.endswith(".txt") or filename == "Dockerfile"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    modified = False
                    # Remove python markdown wrapper lines
                    if content.startswith("```python"):
                        content = content[len("```python"):].strip()
                        modified = True
                    elif content.startswith("```"):
                        content = content[3:].strip()
                        modified = True
                    
                    # Remove trailing backticks
                    if content.endswith("```"):
                        content = content[:-3].strip()
                        modified = True
                    
                    if modified:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"🧹 Central Cleanup: Cleaned markdown wrappers from {filepath}")
                except Exception as e:
                    print(f"Error cleaning {filepath}: {e}")

def run():
    """
    Run the research crew with a self-healing QA and Frontend loop.
    """
    inputs = {
        'requirements': requirements,
        'module_name': module_name,
        'class_name': class_name
    }

    # 1. Run the initial multi-agent pipeline
    print("🚀 Starting Multi-Agent Development Pipeline...")
    team = EngineeringTeam()
    result = team.crew().kickoff(inputs=inputs)
    print("✅ Initial pipeline execution completed.")
    
    # Clean the generated files immediately after they are written
    clean_output_files()

    # 2. Enter the Backend Self-Healing Loop
    max_retries = 3
    test_file_path = os.path.join('output', f"test_{module_name}")
    code_file_path = os.path.join('output', module_name)
    frontend_file_path = os.path.join('output', 'app.py')

    for attempt in range(1, max_retries + 1):
        print(f"\n🔍 Running Unit Tests (Attempt {attempt}/{max_retries})...")
        
        if not os.path.exists(test_file_path):
            print(f"❌ Test file not found at {test_file_path}. Cannot verify code.")
            break

        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath("output") + os.pathsep + env.get("PYTHONPATH", "")

        run_result = subprocess.run(
            [sys.executable, test_file_path],
            capture_output=True,
            text=True,
            env=env
        )

        if run_result.returncode == 0:
            print("🎉 Success! All unit tests passed.")
            break
        else:
            print("❌ Tests failed. Capturing error traceback...")
            error_trace = run_result.stderr or run_result.stdout
            print(error_trace)

            if attempt == max_retries:
                print("⚠️ Max retries reached. Exiting loop with test failures.")
                break

            print(f"🔄 Triggering Backend Self-Healing: Sending design spec and error trace to Backend Engineer...")
            
            design_file_path = os.path.join('output', f"{module_name}_design.md")
            with open(design_file_path, 'r', encoding='utf-8') as f:
                design_spec = f.read()
            with open(code_file_path, 'r', encoding='utf-8') as f:
                current_code = f.read()
            with open(test_file_path, 'r', encoding='utf-8') as f:
                current_tests = f.read()

            refinement_inputs = {
                'requirements': requirements,
                'module_name': module_name,
                'class_name': class_name,
                'design_spec': design_spec,
                'current_code': current_code,
                'current_tests': current_tests,
                'error_trace': error_trace
            }

            refinement_crew = Crew(
                agents=[team.backend_engineer()],
                tasks=[team.refine_code_task()],
                verbose=True
            )
            refinement_crew.kickoff(inputs=refinement_inputs)
            print("🩹 Backend Engineer updated the code. Cleaning and re-running tests...")
            clean_output_files()

    # 3. Enter the Frontend Smoke Test & Self-Healing Loop
    for attempt in range(1, max_retries + 1):
        print(f"\n🖥️ Running Frontend Smoke Test (Attempt {attempt}/{max_retries})...")
        
        if not os.path.exists(frontend_file_path):
            print(f"❌ Frontend file not found at {frontend_file_path}. Cannot verify UI.")
            break

        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath("output") + os.pathsep + env.get("PYTHONPATH", "")

        # Launch the Gradio app in the background. If it has a NameError/ImportError, it crashes immediately.
        # If it's valid, it will block (keep running). We wait 2 seconds and stop it.
        try:
            proc = subprocess.Popen(
                [sys.executable, frontend_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            # Wait for 2.5 seconds to see if it crashes
            stdout, stderr = proc.communicate(timeout=2.5)
            # If communicate completes, it means the process exited (crashed!)
            print("❌ Frontend crashed on startup!")
            error_trace = stderr or stdout
            print(error_trace)
        except subprocess.TimeoutExpired:
            # If timeout expires, it means the server booted successfully and is blocking!
            print("🎉 Success! Frontend booted successfully without crashing.")
            proc.kill() # Clean up the server process
            break

        if attempt == max_retries:
            print("⚠️ Max retries reached. Exiting loop with frontend failures.")
            break

        print(f"🔄 Triggering Frontend Self-Healing: Sending error trace to Frontend Engineer...")
        with open(code_file_path, 'r', encoding='utf-8') as f:
            backend_code = f.read()
        with open(frontend_file_path, 'r', encoding='utf-8') as f:
            current_frontend = f.read()

        frontend_refinement_inputs = {
            'requirements': requirements,
            'module_name': module_name,
            'class_name': class_name,
            'backend_code': backend_code,
            'current_frontend': current_frontend,
            'error_trace': error_trace
        }

        refinement_crew = Crew(
            agents=[team.frontend_engineer()],
            tasks=[team.refine_frontend_task()],
            verbose=True
        )
        refinement_crew.kickoff(inputs=frontend_refinement_inputs)
        print("🩹 Frontend Engineer updated the UI. Cleaning and re-running smoke test...")
        clean_output_files()
        
if __name__ == "__main__":
    run()