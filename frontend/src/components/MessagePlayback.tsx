import { useEffect, useMemo, useRef, useState } from "react";
import {
  parseMarkup,
  splitEmphasis,
  type MarkupNode,
  type PlaybackSettings,
  DEFAULT_PLAYBACK,
} from "../parser/markup";

interface Props {
  rawContent: string;
  settings?: Partial<PlaybackSettings>;
  /** When true, skip animation and show everything */
  instant?: boolean;
  /** Called when playback finishes */
  onComplete?: () => void;
  className?: string;
}

/**
 * Plays markup content node-by-node without revealing formatting characters.
 * Dialogue appears as quoted speech; actions as italics; etc.
 */
export function MessagePlayback({
  rawContent,
  settings: settingsProp,
  instant = false,
  onComplete,
  className,
}: Props) {
  const settings: PlaybackSettings = { ...DEFAULT_PLAYBACK, ...settingsProp };
  const nodes = useMemo(() => parseMarkup(rawContent), [rawContent]);
  const [visibleCount, setVisibleCount] = useState(instant || !settings.enabled ? nodes.length : 0);
  const [charProgress, setCharProgress] = useState(0); // chars revealed in current node
  const [paused, setPaused] = useState(false);
  const cancelled = useRef(false);

  // Reset when content changes
  useEffect(() => {
    cancelled.current = false;
    if (instant || !settings.enabled) {
      setVisibleCount(nodes.length);
      setCharProgress(0);
      onComplete?.();
      return;
    }
    setVisibleCount(0);
    setCharProgress(0);

    let nodeIdx = 0;
    let charIdx = 0;
    let timer: ReturnType<typeof setTimeout>;

    const pauseFor = (ms: number) =>
      new Promise<void>((resolve) => {
        timer = setTimeout(resolve, ms);
      });

    async function run() {
      await pauseFor(settings.initialDelayMs);
      if (cancelled.current) return;

      while (nodeIdx < nodes.length) {
        if (cancelled.current) return;
        while (paused) {
          await pauseFor(50);
          if (cancelled.current) return;
        }

        const node = nodes[nodeIdx];
        setVisibleCount(nodeIdx);
        setCharProgress(0);

        if (node.type === "break") {
          nodeIdx++;
          setVisibleCount(nodeIdx);
          continue;
        }

        const text = node.text;
        const cps = Math.max(8, settings.charsPerSecond);
        const msPerChar = 1000 / cps;

        for (charIdx = 1; charIdx <= text.length; charIdx++) {
          if (cancelled.current) return;
          while (paused) {
            await pauseFor(50);
            if (cancelled.current) return;
          }
          setCharProgress(charIdx);
          await pauseFor(msPerChar);
        }

        nodeIdx++;
        setVisibleCount(nodeIdx);
        setCharProgress(0);

        // Inter-node pause
        let gap = 80;
        if (node.type === "dialogue") gap = settings.dialoguePauseMs;
        else if (node.type === "action" || node.type === "important-action")
          gap = settings.actionPauseMs;
        else if (node.type === "heading") gap = settings.headingPauseMs;
        await pauseFor(gap);
      }
      onComplete?.();
    }

    run();
    return () => {
      cancelled.current = true;
      clearTimeout(timer!);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rawContent, instant, settings.enabled]);

  function skip() {
    cancelled.current = true;
    setVisibleCount(nodes.length);
    setCharProgress(0);
    onComplete?.();
  }

  function revealAll() {
    skip();
  }

  return (
    <div className={className}>
      <div className="space-y-1.5">
        {nodes.slice(0, visibleCount).map((node, i) => (
          <RenderedNode key={i} node={node} partial={undefined} />
        ))}
        {visibleCount < nodes.length && charProgress > 0 && (
          <RenderedNode
            node={nodes[visibleCount]}
            partial={nodes[visibleCount].text.slice(0, charProgress)}
          />
        )}
      </div>
      {settings.enabled && !instant && visibleCount < nodes.length && (
        <div className="flex gap-2 mt-2">
          <button
            type="button"
            onClick={() => setPaused((p) => !p)}
            className="text-xs text-slate-400 hover:text-white"
          >
            {paused ? "Resume" : "Pause"}
          </button>
          <button
            type="button"
            onClick={revealAll}
            className="text-xs text-slate-400 hover:text-white"
          >
            Skip
          </button>
        </div>
      )}
    </div>
  );
}

function RenderedNode({
  node,
  partial,
}: {
  node: MarkupNode;
  partial?: string;
}) {
  const text = partial ?? node.text;

  switch (node.type) {
    case "break":
      return <div className="h-2" />;
    case "heading":
      return (
        <div className="text-base font-semibold text-slate-100 mt-1 mb-1">
          {text}
        </div>
      );
    case "dialogue":
      return (
        <div className="text-slate-100">
          &ldquo;
          <EmphasisText text={text} />
          &rdquo;
        </div>
      );
    case "action":
      return (
        <div className="text-slate-300 italic">
          <EmphasisText text={text} />
        </div>
      );
    case "important-action":
      return (
        <div className="text-slate-100 italic font-medium">
          <EmphasisText text={text} />
        </div>
      );
    case "bullet":
      return (
        <div className="flex gap-2 text-slate-300">
          <span className="text-accent-muted">•</span>
          <span>
            <EmphasisText text={text} />
          </span>
        </div>
      );
    default:
      return (
        <div className="text-slate-200">
          <EmphasisText text={text} />
        </div>
      );
  }
}

function EmphasisText({ text }: { text: string }) {
  const parts = splitEmphasis(text);
  return (
    <>
      {parts.map((p, i) =>
        p.emphasis ? (
          <strong key={i} className="font-semibold text-slate-50">
            {p.text}
          </strong>
        ) : (p as { italic?: boolean }).italic ? (
          <em key={i} className="italic text-slate-100">
            {p.text}
          </em>
        ) : (
          <span key={i}>{p.text}</span>
        )
      )}
    </>
  );
}

/** Static render without animation (for older messages). */
export function MessageStatic({
  rawContent,
  className,
}: {
  rawContent: string;
  className?: string;
}) {
  const nodes = useMemo(() => parseMarkup(rawContent), [rawContent]);
  return (
    <div className={`space-y-1.5 ${className || ""}`}>
      {nodes.map((node, i) => (
        <RenderedNode key={i} node={node} />
      ))}
    </div>
  );
}
