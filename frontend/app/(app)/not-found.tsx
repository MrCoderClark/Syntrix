import Link from "next/link";
import { Button } from "@/components/ui/Button";
import styles from "./not-found.module.css";

export default function NotFound() {
  return (
    <div className={styles.wrap}>
      <div className={styles.code}>404</div>
      <p className={styles.message}>
        This page doesn&apos;t exist — or you don&apos;t have access.
      </p>
      <Link href="/">
        <Button variant="primary">Back to feed</Button>
      </Link>
    </div>
  );
}
