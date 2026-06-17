"use client";

import styles from "./FeedControls.module.css";

type SortMode = "hot" | "new" | "top";
type Period = "today" | "week" | "month" | "all";

interface Props {
  sort: SortMode;
  period?: Period;
  onSortChange: (sort: SortMode) => void;
  onPeriodChange?: (period: Period) => void;
}

export function FeedControls({
  sort,
  period = "all",
  onSortChange,
  onPeriodChange,
}: Props) {
  return (
    <div className={styles.controls}>
      <div className={styles.tabs}>
        <button
          type="button"
          className={`${styles.tab} ${sort === "hot" ? styles.active : ""}`}
          onClick={() => onSortChange("hot")}
        >
          Hot
        </button>
        <button
          type="button"
          className={`${styles.tab} ${sort === "new" ? styles.active : ""}`}
          onClick={() => onSortChange("new")}
        >
          New
        </button>
        <button
          type="button"
          className={`${styles.tab} ${sort === "top" ? styles.active : ""}`}
          onClick={() => onSortChange("top")}
        >
          Top
        </button>
      </div>

      {sort === "top" && onPeriodChange && (
        <div className={styles.periods}>
          {(["today", "week", "month", "all"] as Period[]).map((p) => (
            <button
              key={p}
              type="button"
              className={`${styles.period} ${period === p ? styles.activePeriod : ""}`}
              onClick={() => onPeriodChange(p)}
            >
              {p === "today"
                ? "Today"
                : p === "week"
                  ? "This Week"
                  : p === "month"
                    ? "This Month"
                    : "All Time"}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
