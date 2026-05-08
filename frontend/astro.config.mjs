import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

export default defineConfig({
  integrations: [tailwind()],
  output: "static",
  build: {
    assets: "assets",
  },
  vite: {
    define: {
      "import.meta.env.PUBLIC_USER_SLUG": JSON.stringify(
        process.env.USER_SLUG ?? "robert",
      ),
      "import.meta.env.PUBLIC_BRAWLER_SUBJECT": JSON.stringify(
        process.env.BRAWLER_SUBJECT ?? "englisch",
      ),
      "import.meta.env.PUBLIC_API_BASE": JSON.stringify(
        process.env.API_BASE ?? "",
      ),
    },
  },
});
