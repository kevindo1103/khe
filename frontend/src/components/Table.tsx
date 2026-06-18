import React from 'react';

interface Column<T> {
  key: keyof T | string;
  label: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  renderCell?: (key: string, row: T) => React.ReactNode;
  className?: string;
}

export function Table<T extends Record<string, unknown>>({
  columns,
  rows,
  renderCell,
  className = '',
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
            <tr key={i} className="border-b border-border">
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
