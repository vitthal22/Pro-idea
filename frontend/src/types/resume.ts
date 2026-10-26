/** TypeScript mirror of backend ResumeResponse (app/api/schemas/resumes.py). */

export interface ResumeResponse {
  id: string;
  original_name: string;
  file_size: number;
  mime_type: string;
  parsing_status: string;
  created_at: string;
}
