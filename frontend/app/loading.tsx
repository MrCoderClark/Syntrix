import styles from "./loading.module.css";

export default function Loading() {
  return (
    <div className={styles.wrap}>
      <div className={styles.dot} />
      <div className={styles.dot} />
      <div className={styles.dot} />
    </div>
  );
}
