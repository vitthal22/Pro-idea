import { ArrowLeft } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms — Resume Roaster",
};

export default function TermsPage() {
  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-12">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Back to the roast
      </Link>

      <h1 className="mt-8 heading-4">
        Terms
      </h1>
      <p className="mt-2 body-6 text-muted-foreground">
        The rules for using Resume Roaster. Short, because this is a small
        personal project.
      </p>

      <div className="mt-8 space-y-8">
        <section>
          <h2 className="heading-6">The service</h2>
          <p className="mt-2 body-6 text-muted-foreground">
            Resume Roaster sends a resume through a set of AI evaluators and
            returns a score, findings, and a written roast. It is feedback, not
            a hiring decision, and the model can be wrong. The project is
            provided as is, with no company behind it and no guarantee that the
            output is accurate or complete.
          </p>
        </section>

        <section>
          <h2 className="heading-6">Your account</h2>
          <p className="mt-2 body-6 text-muted-foreground">
            You need an account to upload a resume. Use an email you can access,
            keep your password to yourself, and treat activity under your
            account as yours. One person per account.
          </p>
        </section>

        <section>
          <h2 className="heading-6">
            Acceptable use
          </h2>
          <p className="mt-2 body-6 text-muted-foreground">
            Upload your own resume, or one you have permission to share. Do not
            upload someone else&apos;s personal data, anything illegal, or files
            built to break or overload the service. Do not try to get around
            the daily limit or the upload checks.
          </p>
        </section>

        <section>
          <h2 className="heading-6">Limits</h2>
          <p className="mt-2 body-6 text-muted-foreground">
            The free tier allows 3 analyses per day. Uploads must be PDF or
            DOCX, no larger than 10 MB, and contain at least 100 words of
            extractable text. A scan without a text layer will be rejected.
          </p>
        </section>

        <section>
          <h2 className="heading-6">Availability</h2>
          <p className="mt-2 body-6 text-muted-foreground">
            This runs on free AI models and a small server. It can be slow, the
            provider may limit requests, and an analysis can fail or come back
            incomplete. There is no uptime promise. If a roast fails, try again
            later; the resume you uploaded stays saved.
          </p>
        </section>

        <section>
          <h2 className="heading-6">Changes</h2>
          <p className="mt-2 body-6 text-muted-foreground">
            These terms are a draft and will change as the app does. The version
            on this page is the current one. If you keep using the site after a
            change, the new version applies.
          </p>
        </section>
      </div>
    </main>
  );
}
