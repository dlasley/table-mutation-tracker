import Link from "next/link";

export default function HelpPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <Link
          href="/"
          className="text-blue-500 hover:underline text-sm"
        >
          ← Calendar
        </Link>
        <h1 className="text-2xl font-bold mt-2">What can Sally help with?</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Ask any of these by voice or text using the Sally widget.
        </p>
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-2">Grades &amp; Classes</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;What are all the current grades?&rdquo;</li>
          <li>&ldquo;What&apos;s the geometry grade?&rdquo;</li>
          <li>&ldquo;Who&apos;s the French teacher?&rdquo;</li>
          <li>&ldquo;Rank the classes by grade.&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Assignments &amp; Scores</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;What was the score on the circumcenter quiz?&rdquo;</li>
          <li>&ldquo;Show me all the geometry assignments.&rdquo;</li>
          <li>&ldquo;How are quizzes vs homework going in geometry?&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Changes &amp; Updates</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;Did any grades change this week?&rdquo;</li>
          <li>&ldquo;Were any assignments added since Monday?&rdquo;</li>
          <li>&ldquo;Which assignments had their scores changed?&rdquo;</li>
          <li>&ldquo;Have any assignments been deleted?&rdquo;</li>
          <li>&ldquo;Were any scores changed on old assignments?&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Flags &amp; Missing Work</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;Are there any missing assignments?&rdquo;</li>
          <li>&ldquo;Show me everything flagged as late.&rdquo;</li>
          <li>&ldquo;Which assignments are marked incomplete?&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Trends &amp; Patterns</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;Is the geometry grade improving?&rdquo;</li>
          <li>&ldquo;What&apos;s the overall trend in English?&rdquo;</li>
          <li>&ldquo;Give me an overall summary of how things are going.&rdquo;</li>
          <li>&ldquo;What should we be worried about?&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Comparisons</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;Compare geometry grades between March 8th and March 25th.&rdquo;</li>
          <li>&ldquo;What changed in English since last week?&rdquo;</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Navigation</h2>
        <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
          <li>&ldquo;Show me English.&rdquo; — navigates to the English class tab</li>
          <li>&ldquo;Go back to the calendar.&rdquo;</li>
          <li>&ldquo;What can you help with?&rdquo; — shows this page</li>
        </ul>
      </section>
    </div>
  );
}
