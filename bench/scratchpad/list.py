
import ollama
import os
import json

def list_models():
    """Return the list of models from Ollama using the sync Client."""
    client = ollama.Client()
    response = client.list()
    return response.models

if __name__ == "__main__":
    models = list_models()
    print("\nModels returned by list_models():")
    client = ollama.Client()
    scratchpad_dir = os.path.dirname(__file__)
    for model in models:
        print("Model fields:")
        for k, v in model.model_dump().items():
            print(f"  {k}: {v}")
        details = getattr(model, 'details', None)
        if details:
            print("  Details fields:")
            for k, v in details.model_dump().items():
                print(f"    {k}: {v}")
        # Call show for this model and write to markdown
        model_name = getattr(model, 'model', None)
        try:
            show_result = client.show(model_name)
            show_dict = show_result.model_dump()
            # Sanitize model name for filename
            safe_model_name = model_name.replace(':', '_').replace('/', '_') if model_name else 'unknown'
            md_filename = os.path.join(scratchpad_dir, f"model-show-{safe_model_name}.md")
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(f"# Ollama Model: `{model_name}`\n\n")
                f.write("## Model Metadata\n\n")
                for k, v in show_dict.items():
                    if isinstance(v, (dict, list)):
                        f.write(f"### {k}\n")
                        f.write("```json\n")
                        f.write(json.dumps(v, indent=2, default=str))
                        f.write("\n```")
                    else:
                        f.write(f"- **{k}**: {v}\n")
                f.write("\n")
            print(f"  Show output written to {md_filename}")
        except Exception as e:
            print(f"  Error calling show(): {e}")
        print()


