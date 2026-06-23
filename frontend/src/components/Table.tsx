import type { ReactNode } from 'react';

interface Column<T> {
  key: keyof T | string;
  label: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  renderCell?: (key: string, row: T) => ReactNode;
  className?: string;
  rowTestId?: (row: T) => string;
  rowDataAttrs?: (row: T) => Record<string, string>;
}

export function Table<T extends object>({
  columns,
  rows,
  renderCell,
  className = '',
  rowTestId,
  rowDataAttrs,
}: TableProps<T>) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={String(c.key)}
                className="text-left px-3 py-2 text-ink-muted font-semibold border-b border-border-strong whitespace-nowrap"
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className="border-b border-border"
              data-testid={rowTestId ? rowTestId(row) : undefined}
              {...(rowDataAttrs ? rowDataAttrs(row) : {})}
            >
              {columns.map((c) => (
                <td
                  key={String(c.key)}
                  className="px-3 py-2"
                  data-label={c.label}
                >
                  {renderCell
                    ? renderCell(String(c.key), row)
                    : String((row as Record<string, unknown>)[c.key as string] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
