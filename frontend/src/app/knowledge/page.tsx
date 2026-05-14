"use client";

import { useEffect, useRef, useState } from "react";
import {
  BookOpen,
  Database,
  ExternalLink,
  Loader2,
  RefreshCw,
  Upload,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import type { KnowledgeSource, KnowledgeStats } from "@/lib/types";
import { toast } from "sonner";

export default function KnowledgePage() {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [ingesting, setIngesting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => {
    Promise.all([api.knowledgeSources(), api.knowledgeStats()])
      .then(([s, st]) => {
        setSources(s);
        setStats(st);
      })
      .catch(() => toast.error("Failed to load knowledge data"));
  };

  useEffect(load, []);

  const handleIngest = async () => {
    setIngesting(true);
    try {
      const res = await api.ingestKnowledge();
      toast.success(res.message);
      load();
    } catch {
      toast.error("Ingestion failed");
    } finally {
      setIngesting(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await api.uploadDocument(file);
      toast.success(res.message);
      load();
    } catch {
      toast.error("Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <BookOpen className="h-6 w-6" />
          Knowledge Base
        </h1>
        <p className="text-muted-foreground mt-1">
          Authoritative sources and document management for the RAG pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Registered Sources
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">
              {stats?.sources_registered ?? "—"}
            </span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground flex items-center gap-1">
              <Database className="h-3 w-3" />
              Indexed Chunks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">
              {stats?.total_chunks ?? "—"}
            </span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="flex gap-2 flex-wrap">
            <Button
              size="sm"
              variant="outline"
              onClick={handleIngest}
              disabled={ingesting}
            >
              {ingesting ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : (
                <RefreshCw className="mr-1 h-3 w-3" />
              )}
              Re-ingest
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : (
                <Upload className="mr-1 h-3 w-3" />
              )}
              Upload
            </Button>
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.md,.docx"
              className="hidden"
              onChange={handleUpload}
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Pre-Registered Authoritative Sources
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Authority</TableHead>
                <TableHead className="hidden md:table-cell">
                  Description
                </TableHead>
                <TableHead className="w-12" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {sources.map((src) => (
                <TableRow key={src.id}>
                  <TableCell className="font-medium text-sm">
                    {src.title}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">
                      {src.source_type.replace("_", " ")}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{src.authority}</TableCell>
                  <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                    {src.description}
                  </TableCell>
                  <TableCell>
                    {src.url && (
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
