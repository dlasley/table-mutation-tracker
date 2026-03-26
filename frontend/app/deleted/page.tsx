import Link from "next/link";
import { computeDeletions } from "@/lib/deletions";
import DeletionsTable from "./DeletionsTable";

export const dynamic = "force-dynamic";

export default async function DeletedPage() {
  const deletions = await computeDeletions();

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-4">
        <Link href="/" className="text-sm text-blue-500 hover:underline">
          &larr; Calendar
        </Link>
      </div>

      <h1 className="text-xl font-semibold mb-4">Deleted Assignments</h1>

      {deletions.length === 0 ? (
        <p className="text-gray-500">No assignments have been deleted.</p>
      ) : (
        <DeletionsTable deletions={deletions} />
      )}
    </div>
  );
}
