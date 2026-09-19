import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    def echo_model(messages, config):
        del config
        return f"Echo: {messages[-1].content}"

    echo_chat = mo.ui.chat(echo_model, prompts=["Smoke test"])
    echo_chat
    return (echo_chat,)


if __name__ == "__main__":
    app.run()
