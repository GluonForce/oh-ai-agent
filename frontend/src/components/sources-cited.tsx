import { Badge } from "@/components/ui/badge";
import { parseSourceCitation } from "@/lib/resource-links";

export function SourcesCitedList({ sources }: { sources: string[] }) {
  if (sources.length === 0) return null;
  return (
    <ul className="space-y-2">
      {sources.map((source, i) => {
        const { title, url } = parseSourceCitation(source);
        return (
          <li key={`${i}-${url ?? title}`}>
            {url ? (
              <a
                href={url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex max-w-full items-baseline gap-1 text-sm font-medium underline underline-offset-2"
              >
                <span>{title}</span>
                <span className="break-all text-xs font-normal text-muted-foreground no-underline">
                  {url}
                </span>
              </a>
            ) : (
              <Badge variant="secondary" className="whitespace-normal text-left font-normal">
                {title}
              </Badge>
            )}
          </li>
        );
      })}
    </ul>
  );
}
