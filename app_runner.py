import sys
import os
import io
import time
import queue
import threading
import gradio as ui
import warnings

# Redirect warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Thread-safe stream capture class
class StdoutQueue:
    def __init__(self):
        self.queue = queue.Queue()

    def write(self, data):
        self.queue.put(data)

    def flush(self):
        pass

def run_agents_live(reqs, module, clazz, openai_key, gemini_key):
    # 1. Inject API Keys into the environment for this run
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key

    # Import dependencies inside the function so environment variables are loaded
    from engineering_team.crew import EngineeringTeam
    import main as pipeline

    # Update global configs in main
    pipeline.requirements = reqs
    pipeline.module_name = module
    pipeline.class_name = clazz

    # 2. Redirect stdout to capture agent logs
    captured_output = StdoutQueue()
    old_stdout = sys.stdout
    sys.stdout = captured_output

    # 3. Run the pipeline in a separate thread so Gradio can stream logs
    thread = threading.Thread(target=pipeline.run)
    thread.start()

    log_buffer = ""
    # 4. Stream logs live to UI until the thread finishes
    while thread.is_alive() or not captured_output.queue.empty():
        try:
            # Check for new logs
            new_log = captured_output.queue.get(timeout=0.1)
            log_buffer += new_log
            yield log_buffer
        except queue.Empty:
            yield log_buffer

    # Restore stdout
    sys.stdout = old_stdout
    yield log_buffer + "\n\n🎉 Pipeline completed successfully!"

# 5. Build Gradio UI
with ui.Blocks(theme=ui.themes.Soft()) as demo:
    ui.Markdown("# 🤖 Self-Healing Multi-Agent Software Factory")
    ui.Markdown("Specify your requirements, enter your API keys, and watch the agents collaborate live.")
    
    with ui.Row():
        with ui.Column(scale=1):
            reqs_input = ui.Textbox(
                label="High-Level Requirements", 
                value=pipeline.requirements, 
                lines=10
            )
            module_input = ui.Textbox(label="Module Name", value="accounts.py")
            clazz_input = ui.Textbox(label="Class Name", value="Account")
            
            openai_api_input = ui.Textbox(label="OpenAI API Key (Optional)", type="password")
            gemini_api_input = ui.Textbox(label="Gemini API Key (Optional)", type="password")
            
            run_btn = ui.Button("Launch Crew Agents 🚀", variant="primary")
            
        with ui.Column(scale=2):
            ui.Markdown("### Agent Console Logs (Live Stream)")
            console_output = ui.Code(
                label="Terminal Output", 
                language="markdown", 
                lines=25
            )

    run_btn.click(
        run_agents_live, 
        inputs=[reqs_input, module_input, clazz_input, openai_api_input, gemini_api_input], 
        outputs=[console_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7862)