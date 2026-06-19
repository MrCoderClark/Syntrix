import katex from "katex";

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const input = JSON.parse(Buffer.concat(chunks).toString("utf-8"));

const results = input.map(({ latex, displayMode }) => {
  try {
    return {
      html: katex.renderToString(latex, {
        displayMode: Boolean(displayMode),
        throwOnError: false,
        output: "html",
      }),
      error: null,
    };
  } catch (e) {
    return { html: null, error: e.message };
  }
});

process.stdout.write(JSON.stringify(results));
