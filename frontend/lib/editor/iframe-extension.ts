import { Node, mergeAttributes } from "@tiptap/core";

export interface IframeOptions {
  allowFullscreen: boolean;
  HTMLAttributes: Record<string, string>;
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    iframe: {
      setIframe: (options: { src: string }) => ReturnType;
    };
  }
}

export const Iframe = Node.create<IframeOptions>({
  name: "iframe",
  group: "block",
  atom: true,
  selectable: true,
  draggable: true,

  addOptions() {
    return {
      allowFullscreen: true,
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      src: { default: null },
      width: { default: "100%" },
      height: { default: "360" },
      frameborder: { default: "0" },
      allowfullscreen: { default: this.options.allowFullscreen },
    };
  },

  parseHTML() {
    return [{ tag: "iframe" }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      { class: "iframe-wrapper" },
      ["iframe", mergeAttributes(this.options.HTMLAttributes, HTMLAttributes)],
    ];
  },

  addNodeView() {
    return ({ node, editor, getPos }) => {
      const wrapper = document.createElement("div");
      wrapper.classList.add("iframe-placeholder");
      wrapper.title = "Double-click to edit URL";

      const icon = document.createElement("span");
      icon.classList.add("iframe-placeholder-icon");
      icon.textContent = "▶";
      wrapper.appendChild(icon);

      const url = document.createElement("span");
      url.classList.add("iframe-placeholder-url");
      url.textContent = node.attrs.src || "No URL";
      wrapper.appendChild(url);

      wrapper.addEventListener("dblclick", () => {
        const newSrc = prompt("Edit embed URL:", node.attrs.src || "");
        if (newSrc !== null && newSrc !== node.attrs.src) {
          const pos = getPos();
          if (pos === undefined) return;
          editor.view.dispatch(
            editor.view.state.tr.setNodeMarkup(pos, undefined, {
              ...node.attrs,
              src: newSrc,
            }),
          );
        }
      });

      return {
        dom: wrapper,
        selectNode() {
          wrapper.classList.add("selected");
        },
        deselectNode() {
          wrapper.classList.remove("selected");
        },
      };
    };
  },

  addCommands() {
    return {
      setIframe:
        (options) =>
        ({ tr, dispatch }) => {
          const { selection } = tr;
          const node = this.type.create(options);
          if (dispatch) {
            tr.replaceRangeWith(selection.from, selection.to, node);
          }
          return true;
        },
    };
  },
});
