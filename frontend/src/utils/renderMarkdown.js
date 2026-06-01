/**
 * Shared utility to render basic legal markdown (headings, bullets, bolding) to HTML.
 * Also handles escaping to protect against basic injection.
 */
export const renderMarkdown = (text) => {
  if (!text) return "";
  let escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Bold (**text**)
  escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  
  // Parse line by line
  const lines = escaped.split("\n");
  const parsedLines = lines.map(line => {
    const trimmed = line.trim();
    
    // Headings
    if (trimmed.startsWith("### ")) {
      return `<h4 style="font-family: var(--font-serif); color: var(--accent-gold-light); margin: 12px 0 6px 0; font-size: 1.05rem; font-weight: 600;">${trimmed.substring(4)}</h4>`;
    }
    if (trimmed.startsWith("## ")) {
      return `<h3 style="font-family: var(--font-serif); color: var(--accent-gold-light); margin: 16px 0 8px 0; font-size: 1.15rem; font-weight: 600; border-bottom: 1px solid rgba(201,168,76,0.15); padding-bottom: 4px;">${trimmed.substring(3)}</h3>`;
    }
    if (trimmed.startsWith("# ")) {
      return `<h2 style="font-family: var(--font-serif); color: var(--accent-gold); margin: 20px 0 10px 0; font-size: 1.3rem; font-weight: 700;">${trimmed.substring(2)}</h2>`;
    }
    
    // Bullet points
    if (trimmed.startsWith("* ") || trimmed.startsWith("- ") || trimmed.startsWith("• ")) {
      const bulletText = trimmed.startsWith("• ") ? trimmed.substring(2) : (trimmed.startsWith("* ") || trimmed.startsWith("- ")) ? trimmed.substring(2) : trimmed;
      return `<span style="color: var(--accent-gold); margin-right: 6px;">•</span> ${bulletText}`;
    }
    return line;
  });
  
  return parsedLines.join("\n");
};
