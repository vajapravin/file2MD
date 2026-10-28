import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { convertSingleFile, convertUrl } from "../src/services/convertApi";

describe("convertSingleFile", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("handles fast-path synchronous conversion (200 OK)", async () => {
    const mockResponse = {
      filename: "test.txt",
      original_format: "txt",
      markdown: "# Converted Text Content",
      metadata: {
        size_bytes: 25,
        conversion_time_ms: 12,
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue(mockResponse),
    } as unknown as Response);

    const file = new File(["sample content"], "test.txt", {
      type: "text/plain",
    });
    const result = await convertSingleFile(file);

    expect(result.markdown).toBe("# Converted Text Content");
    expect(result.filename).toBe("test.txt");
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("handles asynchronous parallel chunking with 202 Accepted and polling", async () => {
    const initialJob = {
      job_id: "job-abc",
      status: "pending",
      progress: 0,
      filename: "large.pdf",
      extension: ".pdf",
      size_bytes: 10000,
    };

    const inProgressJob = {
      ...initialJob,
      status: "processing",
      progress: 50,
    };

    const completedJob = {
      ...initialJob,
      status: "completed",
      progress: 100,
      markdown: "# Complete PDF Markdown",
      conversion_time_ms: 350,
      chunks_total: 3,
    };

    const progressUpdates: string[] = [];

    let pollCount = 0;
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/convert")) {
        return Promise.resolve({
          ok: true,
          status: 202,
          json: () => Promise.resolve(initialJob),
        });
      }
      if (url.includes("/jobs/job-abc")) {
        pollCount++;
        if (pollCount === 1) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(inProgressJob),
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(completedJob),
        });
      }
      return Promise.reject(new Error(`Unexpected url: ${url}`));
    });

    const file = new File(["%PDF-1.7..."], "large.pdf", {
      type: "application/pdf",
    });
    const result = await convertSingleFile(file, (job) => {
      progressUpdates.push(job.status);
    });

    expect(result.markdown).toBe("# Complete PDF Markdown");
    expect(result.filename).toBe("large.pdf");
    expect(result.metadata.parallel_chunks).toBe(3);
    expect(progressUpdates).toContain("pending");
    expect(progressUpdates).toContain("completed");
  });

  it("throws clear error when conversion endpoint returns error", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: vi
        .fn()
        .mockResolvedValue({ detail: "Unsupported file format '.xyz'." }),
    } as unknown as Response);

    const file = new File(["bad data"], "doc.xyz", {
      type: "application/octet-stream",
    });
    await expect(convertSingleFile(file)).rejects.toThrow(
      "Unsupported file format '.xyz'.",
    );
  });

  it("handles non-JSON error response from proxy gracefully", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
      statusText: "Bad Gateway",
      json: vi
        .fn()
        .mockRejectedValue(new SyntaxError("Unexpected token < in JSON")),
    } as unknown as Response);

    const file = new File(["content"], "doc.txt", {
      type: "text/plain",
    });
    await expect(convertSingleFile(file)).rejects.toThrow(
      "File conversion failed (Bad Gateway).",
    );
  });
});

describe("convertUrl", () => {
  it("converts public web page URL to clean Markdown", async () => {
    const mockResponse = {
      filename: "Markdown_Article.html",
      original_format: "url",
      markdown: "# Markdown Spec\n\nConverted text.",
      metadata: {
        size_bytes: 1200,
        conversion_time_ms: 180,
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue(mockResponse),
    } as unknown as Response);

    const result = await convertUrl("https://en.wikipedia.org/wiki/Markdown");
    expect(result.original_format).toBe("url");
    expect(result.markdown).toContain("Markdown Spec");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/convert/url"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ url: "https://en.wikipedia.org/wiki/Markdown" }),
      }),
    );
  });

  it("handles forbidden private network address errors", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: vi.fn().mockResolvedValue({
        detail: "Access to private or local network addresses is prohibited.",
      }),
    } as unknown as Response);

    await expect(convertUrl("http://192.168.1.1/admin")).rejects.toThrow(
      "Access to private or local network addresses is prohibited.",
    );
  });
});
