import type { MetadataRoute } from "next";
import { products } from "@/lib/products";
import { site } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const staticRoutes = ["", "/tienda"].map((path) => ({
    url: `${site.url}${path}`,
    lastModified: new Date(),
  }));

  const productRoutes = products.map((p) => ({
    url: `${site.url}/producto/${p.slug}`,
    lastModified: new Date(),
  }));

  return [...staticRoutes, ...productRoutes];
}
