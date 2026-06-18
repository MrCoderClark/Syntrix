import CodeBlockLowlight from "@tiptap/extension-code-block-lowlight";
import Image from "@tiptap/extension-image";
import Link from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";
import { common, createLowlight } from "lowlight";

import { Iframe } from "./iframe-extension";

const lowlight = createLowlight(common);

export function getSyntrixExtensions(placeholder?: string) {
  return [
    StarterKit.configure({ codeBlock: false }),
    Image.configure({ inline: true, allowBase64: false }),
    Link.configure({ openOnClick: false, autolink: true }),
    CodeBlockLowlight.configure({ lowlight }),
    Iframe,
    Placeholder.configure({
      placeholder: placeholder ?? "Write something...",
    }),
  ];
}
