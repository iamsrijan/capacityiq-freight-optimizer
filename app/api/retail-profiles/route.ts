import { siteDataset } from "@/app/lib/site-dataset";

export async function GET() {
  return Response.json(siteDataset.retailProfiles);
}
