import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import type { User } from "../types";

interface UserPickerProps {
  users: User[];
  value: string;
  onChange: (userId: string) => void;
  placeholder?: string;
}

export default function UserPicker({ users, value, onChange, placeholder = "Search by name or email..." }: UserPickerProps) {
  const selected = users.find((u) => u.id === value) ?? null;
  const [query, setQuery] = useState(selected ? selected.display_name : "");
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setQuery(selected ? selected.display_name : "");
  }, [selected?.id]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
        setQuery(selected ? selected.display_name : "");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [selected]);

  const matches =
    query.trim() === ""
      ? users
      : users.filter(
          (u) =>
            u.display_name.toLowerCase().includes(query.toLowerCase()) ||
            u.email.toLowerCase().includes(query.toLowerCase())
        );
  const visibleMatches = matches.slice(0, 2);

  function selectUser(user: User) {
    onChange(user.id);
    setQuery(user.display_name);
    setOpen(false);
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (!open) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlighted((h) => Math.min(h + 1, visibleMatches.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlighted((h) => Math.max(h - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      const user = visibleMatches[highlighted];
      if (user) selectUser(user);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div className="user-picker" ref={ref}>
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
          setHighlighted(0);
          if (value) onChange("");
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoComplete="off"
      />
      {open && visibleMatches.length > 0 && (
        <div className="user-picker-dropdown">
          {visibleMatches.map((u, i) => (
            <div
              key={u.id}
              className={`user-picker-option ${i === highlighted ? "highlighted" : ""}`}
              onMouseDown={() => selectUser(u)}
              onMouseEnter={() => setHighlighted(i)}
            >
              <span className="user-picker-name">{u.display_name}</span>
              <span className="user-picker-email">{u.email}</span>
            </div>
          ))}
        </div>
      )}
      {open && query.trim() !== "" && visibleMatches.length === 0 && (
        <div className="user-picker-dropdown">
          <div className="user-picker-empty">No matching users</div>
        </div>
      )}
    </div>
  );
}
