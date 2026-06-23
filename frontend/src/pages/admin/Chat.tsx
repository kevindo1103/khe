import { useState, useRef, useEffect } from 'react';
import { Button, Input } from '../../components';
import { apiFetch } from '../../lib/api';
import type { ChatMessage, ChatQueryOut, ChatSource } from '../../types/chat';
import type { ApiError } from '../../lib/api';
import { OBLIGATION_TYPE_LABELS, labelFor } from '../../lib/labels';

const D08_MAIN = 'Không tìm thấy thông tin này trong hồ sơ của bạn.';
const D08_SUB =
  'Khế chỉ trả lời từ tài liệu bạn đã tải lên — không phỏng đoán. Bạn có thể hỏi cách khác hoặc tải thêm tài liệu.';

const SUGGESTION_CHIPS = [
  'Cái gì sắp hết hạn?',
  'Tìm HĐ với Hải Đăng',
  'HĐ thuê MB còn hạn bao lâu?',
  'Còn mấy đợt thanh toán?',
  'Việc gì đang chờ sự kiện?',
];

function SourceChip({ source }: { source: ChatSource }) {
  const isObligation = source.type === 'obligation';
  return (
    <div className="flex flex-wrap gap-1.5 items-center">
      <span className="inline-flex items-center gap-1 bg-primary-soft text-primary border border-primary/20 rounded-full px-2.5 py-0.5 text-2xs font-medium">
        📄 {source.file_name}
        {source.clause_num ? ` · ${source.clause_num}` : ''}
      </span>
      {isObligation && source.obligation_type && (
        <span className="inline-flex items-center bg-ink-muted/10 text-ink-muted border border-border rounded-full px-2 py-0.5 text-2xs font-medium">
          {labelFor(OBLIGATION_TYPE_LABELS, source.obligation_type)}
        </span>
      )}
      {isObligation && source.milestone_total && source.milestone_total > 1 && source.milestone_index != null && (
        <span className="inline-flex items-center bg-info-soft text-info border border-info/20 rounded-full px-2 py-0.5 text-2xs font-medium">
          Đợt {source.milestone_index}/{source.milestone_total}
        </span>
      )}
      {isObligation && source.status === 'waiting_trigger' && source.trigger_condition && (
        <span className="inline-flex items-center bg-warning-soft text-warning border border-warning/20 rounded-full px-2 py-0.5 text-2xs font-medium">
          ⏳ Chờ: {source.trigger_condition}
        </span>
      )}
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const { role, text, source, notFound, isError, loading: isLoading } = message;

  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[78%] bg-primary text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed shadow-sm">
          {text}
        </div>
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="flex justify-start max-w-[88%]">
        <div className="bg-warning-soft border border-warning/30 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed">
          <div className="text-warning font-semibold mb-1">{D08_MAIN}</div>
          <div className="text-warning/90 text-xs">{D08_SUB}</div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-start">
        <div className="bg-surface border border-border rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm text-ink-muted italic shadow-sm">
          Đang tìm…
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1.5 items-start max-w-[88%]">
      <div
        className={`rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
          isError
            ? 'bg-danger-soft border border-danger/30 text-danger'
            : 'bg-surface border border-border text-ink'
        }`}
      >
        {source?.direction === 'nghĩa_vụ' && (
          <span className="font-semibold text-primary">Bạn cần </span>
        )}
        {source?.direction === 'quyền_lợi' && (
          <span className="font-semibold text-primary">Đối tác cần </span>
        )}
        {text}
      </div>
      {source && <SourceChip source={source} />}
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async (question: string) => {
    if (!question.trim() || loading) return;

    const userMsg: ChatMessage = { role: 'user', text: question };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await apiFetch<ChatQueryOut>('/chat/query', {
        method: 'POST',
        body: JSON.stringify({ question }),
      });
      const notFound = !data.found;
      const botMsg: ChatMessage = {
        role: 'bot',
        text: data.answer || null,
        source: data.sources?.[0] || null,
        notFound,
      };
      setMessages((m) => [...m, botMsg]);
    } catch (err) {
      const apiErr = err as ApiError;
      setMessages((m) => [
        ...m,
        {
          role: 'bot',
          text: `Lỗi: ${apiErr.message}`,
          source: null,
          notFound: false,
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleChip = (chip: string) => {
    setInput(chip);
    sendMessage(chip);
  };

  const showEmpty = messages.length === 0 && !loading;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-3xl mx-auto">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 px-2 space-y-3">
        {showEmpty ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 py-16 text-center">
            <div className="text-5xl">💬</div>
            <div className="text-lg font-semibold text-ink">
              Hỏi Khế về hợp đồng của bạn
            </div>
            <div className="text-sm text-ink-muted max-w-sm leading-relaxed">
              Khế tìm thông tin từ tài liệu bạn đã tải lên và nhắc bạn trước khi hợp
              đồng hết hạn.
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <ChatBubble key={i} message={msg} />
            ))}
            {loading && (
              <ChatBubble message={{ role: 'bot', text: 'Đang tìm…', loading: true }} />
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Suggestion chips */}
      {showEmpty && (
        <div className="px-2 pb-3">
          <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
            {SUGGESTION_CHIPS.map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => handleChip(chip)}
                className="whitespace-nowrap px-3 py-1.5 bg-primary-soft text-primary border border-primary/20 rounded-full text-xs font-medium hover:bg-primary/10 transition-colors cursor-pointer flex-shrink-0"
              >
                {chip}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-border bg-surface p-3 rounded-b-lg">
        {messages.length > 0 && !showEmpty && (
          <div className="flex gap-2 overflow-x-auto pb-2 mb-1" style={{ scrollbarWidth: 'none' }}>
            {SUGGESTION_CHIPS.map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => handleChip(chip)}
                className="whitespace-nowrap px-3 py-1 bg-primary-soft text-primary border border-primary/20 rounded-full text-xs font-medium hover:bg-primary/10 transition-colors cursor-pointer flex-shrink-0"
              >
                {chip}
              </button>
            ))}
          </div>
        )}
        <form onSubmit={handleSubmit} className="flex gap-2 items-center">
          <div className="flex-1">
            <Input
              value={input}
              onChange={setInput}
              placeholder="Hỏi về hợp đồng của bạn…"
              className="mb-0"
            />
          </div>
          <Button
            type="submit"
            size="sm"
            disabled={!input.trim() || loading}
            className="flex-shrink-0 h-11 w-11 px-0 rounded-full"
          >
            ➤
          </Button>
        </form>
        {/* TODO(#96): remove when backend #96 merges (Unicode doc-hint + expiring_within + find_by_party) */}
        <div className="mt-2 text-center text-2xs text-ink-subtle">
          Tính năng tìm kiếm nâng cao đang được cải thiện.
        </div>
      </div>
    </div>
  );
}
