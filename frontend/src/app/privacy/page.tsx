import { ArrowLeft } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy — Resume Roaster",
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-12">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Back to the roast
      </Link>

      <p className="mt-8 font-mono text-xs text-muted-foreground">
        Plain language draft, last updated 7 November 2026.
      </p>
      <h1 className="mt-2 heading-4">
        Privacy
      </h1>
      <p className="mt-2 body-6 text-muted-foreground">
        The short version: your resume is stored so you can come back to it,
        and its text goes to one AI provider to produce the roast.
      </p>

      <div className="mt-8 space-y-8">
        <section>
          <h2 className="heading-6">What we store</h2>
          <p className="mt-2 body-6 text-muted-foreground">
            Your account email and a bcrypt hash of your password. The password
            itself is never stored. Uploaded resumes are saved as files under
            the configured upload directory, one folder per user, along with
            the text extracted from them. Roast results are stored too, with
            the model name and the input and output token counts for each AI
            call, so usage and cost can be tracked.
          </p>
        </section>

        <section>
          <h2 className="heading-6">Where it goes</h2>
          <p className="mt-2 body-6 text-muted-foreground">
            To produce a roast, the text you submit goes to the AI model
            provider configured for this deployment: your resume, plus any job
            description or focus note you add. That provider handles the text
            under its own terms and retention rules. Nothing else leaves this
            server. There are no analytics scripts, advertising networks, or
            trackers from other companies.
          </p>
        </section>

        <section>
          <h2 className="heading-6">
            Cookies and sessions
          </h2>
          <p className="mt-2 body-6 text-muted-foreground">
            Signing in returns an access token that lasts 1 hour and is kept in
            your browser&apos;s local storage, plus a refresh token in an
            HttpOnly cookie that lasts 7 days. The cookie is SameSite=Lax,
            scoped to the auth API path, and marked Secure in production. Both
            exist to keep you signed in. There are no tracking or advertising
            cookies, and logging out revokes the refresh token.
          </p>
        </section>

        <section>
          <h2 className="heading-6">
            Deleting your data
          </h2>
          <p className="mt-2 body-6 text-muted-foreground">
            Deleting a resume removes its file from storage and marks the
            database row as deleted, so it stops showing up in the app. The row
            itself, and the results built from it, stay in the database. There
            is no button to delete your whole account yet; ask and the account,
            its resumes, and its results will be removed by hand.
          </p>
        </section>

        <section>
          <h2 className="heading-6">Contact</h2>
          <p className="mt-2 body-6 text-muted-foreground">
            This is a small personal project, not a company. There is no
            support desk and no data protection officer. If you want your data
            removed or have a question about it, reply wherever you found this
            project and I will sort it out.
          </p>
        </section>
      </div>
    </main>
  );
}
