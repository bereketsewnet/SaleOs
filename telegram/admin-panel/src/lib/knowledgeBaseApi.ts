import { api } from "./api";

export interface KnowledgeFile {
  id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  status: "processing" | "ready" | "failed";
  error_message: string | null;
  chunk_count: number;
  uploaded_at: string;
}

export async function listKnowledgeFiles(): Promise<KnowledgeFile[]> {
  const { data } = await api.get<KnowledgeFile[]>("/api/v1/core/knowledge-base/");
  return data;
}

export async function uploadKnowledgeFile(file: File): Promise<KnowledgeFile> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<KnowledgeFile>(
    "/api/v1/core/knowledge-base/",
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

export async function deleteKnowledgeFile(id: string): Promise<void> {
  await api.delete(`/api/v1/core/knowledge-base/${id}`);
}
