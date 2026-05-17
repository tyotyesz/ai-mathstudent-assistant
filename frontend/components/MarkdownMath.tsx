"use client";

import katex from "katex";

type Props = {
  content: string;
  className?: string;
};

type Token = {
  type: "text" | "inline" | "block";
  value: string;
};

const defaultClassName = "text-sm text-slate-700 whitespace-pre-wrap break-words";

const isEscaped = (text: string, index: number) => {
  let backslashes = 0;
  let idx = index - 1;
  while (idx >= 0 && text[idx] === "\\") {
    backslashes += 1;
    idx -= 1;
  }
  return backslashes % 2 === 1;
};

const normalizeMathDelimiters = (text: string) => {
  let normalized = text;
  normalized = normalized.replace(/\\\\\[(.+?)\\\\\]/gs, (_match, body) => `$$${body}$$`);
  normalized = normalized.replace(/\\\[(.+?)\\\]/gs, (_match, body) => `$$${body}$$`);
  normalized = normalized.replace(/\\\\\((.+?)\\\\\)/g, (_match, body) => `$${body}$`);
  normalized = normalized.replace(/\\\((.+?)\\\)/g, (_match, body) => `$${body}$`);
  return normalized;
};

const splitMathTokens = (text: string): Token[] | null => {
  const tokens: Token[] = [];
  let buffer = "";
  let idx = 0;

  const pushText = () => {
    if (buffer) {
      tokens.push({ type: "text", value: buffer });
      buffer = "";
    }
  };

  const findClosingDouble = (start: number) => {
    for (let i = start; i < text.length - 1; i += 1) {
      if (text[i] === "$" && text[i + 1] === "$" && !isEscaped(text, i)) {
        return i;
      }
    }
    return -1;
  };

  const findClosingSingle = (start: number) => {
    for (let i = start; i < text.length; i += 1) {
      if (text[i] !== "$") continue;
      if (text[i + 1] === "$" && !isEscaped(text, i)) {
        return -1;
      }
      if (!isEscaped(text, i)) {
        return i;
      }
    }
    return -1;
  };

  while (idx < text.length) {
    if (text[idx] === "$" && text[idx + 1] === "$" && !isEscaped(text, idx)) {
      pushText();
      const end = findClosingDouble(idx + 2);
      if (end === -1) return null;
      tokens.push({ type: "block", value: text.slice(idx + 2, end) });
      idx = end + 2;
      continue;
    }
    if (text[idx] === "$" && !isEscaped(text, idx)) {
      pushText();
      const end = findClosingSingle(idx + 1);
      if (end === -1) return null;
      tokens.push({ type: "inline", value: text.slice(idx + 1, end) });
      idx = end + 1;
      continue;
    }
    buffer += text[idx];
    idx += 1;
  }

  pushText();
  return tokens;
};

const renderMath = (value: string, displayMode: boolean) => {
  try {
    const html = katex.renderToString(value, {
      throwOnError: false,
      displayMode,
    });
    return (
      <span
        className={displayMode ? "block my-2" : "inline"}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  } catch {
    return <span>{displayMode ? `$$${value}$$` : `$${value}$`}</span>;
  }
};

export default function MarkdownMath({ content, className }: Props) {
  const normalized = normalizeMathDelimiters(content);
  const tokens = splitMathTokens(normalized);
  if (!tokens) {
    return <div className={className ?? defaultClassName}>{content}</div>;
  }

  return (
    <div className={className ?? defaultClassName}>
      {tokens.map((token, index) => {
        if (token.type === "text") {
          return <span key={index}>{token.value}</span>;
        }
        if (token.type === "block") {
          return <span key={index}>{renderMath(token.value, true)}</span>;
        }
        return <span key={index}>{renderMath(token.value, false)}</span>;
      })}
    </div>
  );
}
