import styles from "./PostCardSkeleton.module.css";

export function PostCardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className={styles.feed}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={styles.card}>
          <div className={styles.voteCol}>
            <div className={styles.bone} style={{ width: 24, height: 60 }} />
          </div>
          <div className={styles.content}>
            <div className={styles.bone} style={{ width: "30%", height: 12 }} />
            <div
              className={styles.bone}
              style={{ width: "80%", height: 16, marginTop: 6 }}
            />
            <div
              className={styles.bone}
              style={{ width: "60%", height: 12, marginTop: 10 }}
            />
            <div className={styles.metaRow}>
              <div
                className={`${styles.bone} ${styles.circle}`}
                style={{ width: 24, height: 24 }}
              />
              <div className={styles.bone} style={{ width: 80, height: 12 }} />
              <div className={styles.bone} style={{ width: 40, height: 12 }} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
