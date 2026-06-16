import styles from "./Wordmark.module.css";

export function Wordmark() {
  return (
    <span className={styles.wordmark}>
      Syntrix<span className={styles.dot}>.</span>
    </span>
  );
}
