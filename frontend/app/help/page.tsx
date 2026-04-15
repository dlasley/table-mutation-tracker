import Link from "next/link";

function NavBadge({ label = "opens view" }: { label?: string }) {
  return (
    <span className="ml-1.5 text-xs text-blue-500 dark:text-blue-400 font-normal">
      → {label}
    </span>
  );
}

export default function HelpPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <Link href="/" className="text-blue-500 hover:underline text-sm">
          ← Calendar
        </Link>
        <h1 className="text-2xl font-bold mt-2">What can Sally help with?</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Ask any of these by voice using the Sally widget. Items marked{" "}
          <span className="text-blue-500 dark:text-blue-400 text-xs font-medium">
            → opens view
          </span>{" "}
          will also navigate the browser to the relevant data.
        </p>
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-2">Grades &amp; Classes</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;What are all the current grades?&rdquo;</li>
          <li>
            &ldquo;What&apos;s the geometry grade?&rdquo;
            <NavBadge label="geometry tab" />
          </li>
          <li>
            &ldquo;What was the geometry grade last Friday?&rdquo;
            <NavBadge label="that day, geometry tab" />
          </li>
          <li>&ldquo;Who&apos;s the French teacher?&rdquo;</li>
          <li>&ldquo;Rank the classes by grade.&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Assignments &amp; Scores</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>
            &ldquo;Show me all the geometry assignments.&rdquo;
            <NavBadge label="geometry tab" />
          </li>
          <li>
            &ldquo;What was the score on the circumcenter quiz?&rdquo;
            <NavBadge label="geometry tab" />
          </li>
          <li>
            &ldquo;How are quizzes vs homework going in geometry?&rdquo;
            <NavBadge label="geometry tab" />
          </li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Comparisons</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>
            &ldquo;Compare geometry from last Friday to the Friday before.&rdquo;
            <NavBadge label="comparison view" />
          </li>
          <li>
            &ldquo;Compare geometry grades between March 8th and March 25th.&rdquo;
            <NavBadge label="comparison view" />
          </li>
          <li>&ldquo;What changed in English since last week?&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Changes &amp; Updates</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;Did any grades change this week?&rdquo;</li>
          <li>&ldquo;Were any assignments added since Monday?&rdquo;</li>
          <li>&ldquo;Which assignments had their scores changed?&rdquo;</li>
          <li>&ldquo;Have any assignments been deleted?&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Flags &amp; Missing Work</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>
            &ldquo;Are there any missing assignments?&rdquo;
            <NavBadge label="class tab" />
          </li>
          <li>
            &ldquo;Show me everything flagged as late.&rdquo;
            <NavBadge label="class tab" />
          </li>
          <li>
            &ldquo;Which assignments are marked incomplete?&rdquo;
            <NavBadge label="class tab" />
          </li>
          <li>&ldquo;What hasn&apos;t been graded yet?&rdquo;</li>
          <li>&ldquo;What are the highest-value assignments with no score?&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Trends &amp; Big Picture</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;Is the geometry grade improving?&rdquo;</li>
          <li>&ldquo;What&apos;s the overall trend in English?&rdquo;</li>
          <li>&ldquo;Give me an overall summary of how things are going.&rdquo;</li>
          <li>&ldquo;What should we be worried about?&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Navigation</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>
            &ldquo;Show me English.&rdquo;
            <NavBadge label="English tab" />
          </li>
          <li>&ldquo;Go back to the calendar.&rdquo;</li>
          <li>
            &ldquo;What can you help with?&rdquo;
            <NavBadge label="this page" />
          </li>
        </ul>
      </section>
    </div>
  );
}
