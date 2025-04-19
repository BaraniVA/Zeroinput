from suggestion_engine import build_prompt, ask_phi

prompt = build_prompt()
response = ask_phi(prompt)
print("\n💡 AI Suggestion:")
print(response.strip())
