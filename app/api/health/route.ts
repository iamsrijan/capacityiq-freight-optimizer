import { siteDataset } from "@/app/lib/site-dataset";

export async function GET() {
  return Response.json({
    status: "ok",
    service: "CapacityIQ hosted backend",
    dataset: siteDataset.summary,
  });
}
