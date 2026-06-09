import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getTelegramConfig } from "../../lib/telegramConfigApi";
import {
  getChannelStatus,
  listChannelPosts,
  unbindChannel,
} from "../../lib/telegramChannelApi";
import { useHasRole } from "../RoleGate";

export function ChannelTab() {
  const canEdit = useHasRole(["ADMIN"]);
  const qc = useQueryClient();

  const { data: config } = useQuery({
    queryKey: ["telegramConfig"],
    queryFn: getTelegramConfig,
  });
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ["channelStatus"],
    queryFn: getChannelStatus,
    // Poll every 4s until connected — auto-binding from Telegram is fast.
    refetchInterval: (query) => (query.state.data?.connected ? false : 4000),
  });
  const { data: posts = [] } = useQuery({
    queryKey: ["channelPosts"],
    queryFn: listChannelPosts,
    enabled: !!status?.connected,
    refetchInterval: 8000,
  });

  const unbindMutation = useMutation({
    mutationFn: unbindChannel,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["channelStatus"] });
      qc.invalidateQueries({ queryKey: ["channelPosts"] });
    },
  });

  const botUsername = config?.bot_username;

  if (statusLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-5">
      {/* Status banner */}
      {status?.connected ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 sm:p-5">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">
              Connected
            </span>
            <span className="font-medium text-slate-900">
              {status.channel_title || "Your channel"}
            </span>
            {status.channel_username && (
              <a
                href={`https://t.me/${status.channel_username}`}
                target="_blank"
                rel="noreferrer"
                className="text-sm font-mono text-brand-700 hover:text-brand-800"
              >
                @{status.channel_username}
              </a>
            )}
          </div>
          <p className="text-sm text-slate-700">
            New posts in your channel will be captured automatically.
          </p>
          {canEdit && (
            <button
              onClick={() => {
                if (confirm("Unbind this channel? The bot won't capture new posts until you reconnect.")) {
                  unbindMutation.mutate();
                }
              }}
              disabled={unbindMutation.isPending}
              className="mt-3 text-xs font-medium border border-red-200 text-red-700 hover:bg-red-50 rounded-lg px-3 py-1.5 disabled:opacity-60"
            >
              {unbindMutation.isPending ? "Unbinding…" : "Unbind channel"}
            </button>
          )}
        </div>
      ) : (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 sm:p-5">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
              Not connected
            </span>
          </div>
          <p className="text-sm text-slate-700">
            Follow the steps below. We'll detect your channel automatically.
          </p>
        </div>
      )}

      {/* Step-by-step instructions */}
      {!status?.connected && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h3 className="font-semibold text-slate-900 mb-3">
            Connect your Telegram channel
          </h3>
          <ol className="space-y-3 text-sm text-slate-700">
            <Step n={1}>
              Open <span className="font-medium">your Telegram channel</span> (or
              create one in Telegram if you don't have one yet).
            </Step>
            <Step n={2}>
              Tap the channel name → <span className="font-medium">Administrators</span>
              {" "}→ <span className="font-medium">Add Admin</span>.
            </Step>
            <Step n={3}>
              Search{" "}
              {botUsername ? (
                <span className="font-mono font-medium text-brand-700">@{botUsername}</span>
              ) : (
                <span className="text-red-600">
                  (connect your bot in the Telegram Bot tab first)
                </span>
              )}{" "}
              and add it as an admin.
            </Step>
            <Step n={4}>
              Enable <span className="font-semibold">all three</span> of these
              permissions (uncheck the rest):
              <ul className="list-disc pl-5 mt-1 text-slate-600">
                <li><span className="font-medium">Post messages</span> — bot can publish products</li>
                <li><span className="font-medium">Edit messages</span> — bot can update posts</li>
                <li><span className="font-medium">Delete messages</span> — deleting a product also removes its channel post</li>
              </ul>
              <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-2 py-1.5 mt-1.5">
                Without <span className="font-semibold">Delete messages</span>, the
                bot still works for publishing — but deleting a product here
                won't remove the post from your channel.
              </p>
            </Step>
            <Step n={5}>
              Tap <span className="font-medium">Done</span>. This page will detect
              the connection within a few seconds — no need to type anything.
            </Step>
          </ol>

          <div className="mt-4 rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs text-slate-600">
            <span className="font-semibold text-slate-800">Tip:</span> if you also
            have a linked Discussion Group (so customers can comment under posts),
            add the bot as an admin there too — that's how the AI auto-replies
            work in Phase 8.
          </div>
        </div>
      )}

      {/* Captured posts */}
      {status?.connected && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-900">Recent posts</h3>
            <span className="text-xs text-slate-500">
              Latest {posts.length} · auto-captured
            </span>
          </div>
          {posts.length === 0 ? (
            <p className="text-sm text-slate-500">
              No posts captured yet. Post something in your channel — it'll appear
              here within a few seconds.
            </p>
          ) : (
            <ul className="divide-y divide-slate-200 max-h-[420px] overflow-y-auto pr-1">
              {posts.map((p) => (
                <li key={p.id} className="py-3 flex items-start gap-3">
                  <div className="shrink-0">
                    {p.photo_file_id ? (
                      <div className="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center text-slate-400">
                        📷
                      </div>
                    ) : (
                      <div className="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center text-slate-400">
                        💬
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-slate-800 line-clamp-2">
                      {p.caption || <span className="text-slate-400 italic">(no caption)</span>}
                    </p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                      <span>{new Date(p.posted_at).toLocaleString()}</span>
                      <span>·</span>
                      <span>
                        {p.posted_by_admin
                          ? "Posted from admin panel"
                          : "Posted manually in Telegram"}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function Step({ n, children }: { n: number; children: React.ReactNode }) {
  return (
    <li className="flex gap-3">
      <span className="shrink-0 w-6 h-6 rounded-full bg-brand-100 text-brand-700 text-xs font-semibold flex items-center justify-center">
        {n}
      </span>
      <span>{children}</span>
    </li>
  );
}
