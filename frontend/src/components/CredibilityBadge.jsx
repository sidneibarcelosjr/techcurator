const CONFIG = {
  high:   { emoji: "🟢", text: "Alta",  cls: "cred-high" },
  medium: { emoji: "🟡", text: "Média", cls: "cred-medium" },
  low:    { emoji: "🔴", text: "Baixa", cls: "cred-low" },
};

const TOOLTIP =
  "Indício de credibilidade baseado em consenso entre fontes e sinais " +
  "textuais (clickbait, atribuição). Não é um veredito de verdadeiro/falso.";

/**
 * Exibe o selo de credibilidade (🟢🟡🔴 + rótulo).
 *
 * Props:
 *   label    — "high" | "medium" | "low" | null/undefined
 *   compact  — se true, omite o prefixo "Credibilidade:" (para cards)
 */
export default function CredibilityBadge({ label, compact = false }) {
  if (!label || !CONFIG[label]) return null;
  const { emoji, text, cls } = CONFIG[label];
  return (
    <span className={`cred-badge ${cls}`} title={TOOLTIP}>
      {emoji}{" "}
      {compact ? text : `Credibilidade: ${text}`}
    </span>
  );
}
