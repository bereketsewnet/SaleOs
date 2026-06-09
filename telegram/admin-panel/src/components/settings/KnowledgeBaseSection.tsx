import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteKnowledgeFile,
  listKnowledgeFiles,
  uploadKnowledgeFile,
  type KnowledgeFile,
} from "../../lib/knowledgeBaseApi";
import { useHasRole } from "../RoleGate";

const MAX_FILES = 3;
const ACCEPTED_EXT = ".pdf,.docx,.md,.txt,.xlsx";

export function KnowledgeBaseSection() {
  const canEdit = useHasRole(["ADMIN"]);
  const qc = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: files = [], isLoading } = useQuery({
    queryKey: ["knowledgeBaseFiles"],
    queryFn: listKnowledgeFiles,
    refetchInterval: (q) => {
      const data = q.state.data as KnowledgeFile[] | undefined;
      return data?.some((f) => f.status === "processing") ? 3000 : false;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadKnowledgeFile(file),
    onSuccess: () => {
      setError(null);
      qc.invalidateQueries({ queryKey: ["knowledgeBaseFiles"] });
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      if (typeof detail === "object" && detail?.error === "kb_limit_exceeded") {
        setError(`You can keep at most ${detail.max_files} knowledge files. Delete one first.`);
      } else if (detail === "kb_file_too_large") {
        setError("File too large — max 10 MB.");
      } else if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Upload failed.");
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteKnowledgeFile(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledgeBaseFiles"] }),
  });

  function pick() {
    setError(null);
    fileInputRef.current?.click();
  }

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadMutation.mutate(file);
    e.target.value = "";
  }

  return (
    <div className="border-t border-slate-200 pt-5">
      <div className="flex items-baseline justify-between gap-3 mb-1">
        <h3 className="text-sm font-semibold text-slate-900">
          Knowledge base{" "}
          <span className="text-xs font-normal text-slate-500">
            ({files.length} / {MAX_FILES})
          </span>
        </h3>
      </div>
      <p className="text-xs text-slate-500 mb-3">
        Upload company brochures, FAQ docs, service descriptions, price lists, etc.
        The AI agent reads these whenever a customer asks something. PDF, DOCX, MD,
        TXT, or XLSX — up to 10 MB each, max {MAX_FILES} files. We chunk + embed
        them so the agent only quotes what's relevant to each question.
        Especially recommended for consultancy / service merchants.
      </p>

      {!canEdit && (
        <p className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs px-3 py-2 mb-3">
          Read-only mode. Only ADMIN can manage knowledge files.
        </p>
      )}

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : files.length === 0 ? (
        <p className="text-sm text-slate-500 italic mb-3">
          No documents uploaded yet.
        </p>
      ) : (
        <ul className="space-y-2 mb-3">
          {files.map((f) => (
            <li
              key={f.id}
              className="flex items-center gap-3 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm"
            >
              <FileIcon type={f.file_type} />
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{f.filename}</p>
                <p className="text-xs text-slate-500">
                  <StatusBadge status={f.status} />
                  <span className="ml-2">{f.chunk_count} chunks</span>
                  <span className="ml-2">{prettyBytes(f.size_bytes)}</span>
                </p>
                {f.error_message && (
                  <p className="text-xs text-red-600 mt-1">{f.error_message}</p>
                )}
              </div>
              {canEdit && (
                <button
                  type="button"
                  onClick={() => deleteMutation.mutate(f.id)}
                  disabled={deleteMutation.isPending}
                  className="text-xs text-red-600 hover:text-red-800 font-medium"
                >
                  Remove
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {error && (
        <p className="text-xs text-red-600 mb-2">{error}</p>
      )}

      {canEdit && files.length < MAX_FILES && (
        <>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept={ACCEPTED_EXT}
            onChange={handleFile}
          />
          <button
            type="button"
            onClick={pick}
            disabled={uploadMutation.isPending}
            className="text-sm rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium px-4 py-2 disabled:opacity-50"
          >
            {uploadMutation.isPending ? "Uploading…" : "Upload a document"}
          </button>
        </>
      )}
    </div>
  );
}

function FileIcon({ type }: { type: string }) {
  const map: Record<string, string> = {
    pdf: "📄",
    docx: "📝",
    md: "📋",
    txt: "📋",
    xlsx: "📊",
  };
  return <span className="text-xl">{map[type] ?? "📁"}</span>;
}

function StatusBadge({ status }: { status: KnowledgeFile["status"] }) {
  const tone =
    status === "ready"
      ? "bg-emerald-100 text-emerald-800"
      : status === "processing"
      ? "bg-amber-100 text-amber-800"
      : "bg-red-100 text-red-800";
  return (
    <span className={`inline-block text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${tone}`}>
      {status}
    </span>
  );
}

function prettyBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}
