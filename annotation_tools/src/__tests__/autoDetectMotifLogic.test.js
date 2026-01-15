import { describe, expect, it } from "vitest";

/**
 * Test the logic for auto-detecting motifs/ATU.
 * This tests the section candidate selection logic:
 * - If a section has a summary, use the summary
 * - If a section doesn't have a summary, use the original section text
 * - If whole summary exists and is not empty, use it
 * - If whole summary doesn't exist or is empty, don't use it
 */

describe("Auto Detect Motif/ATU Logic", () => {
  // Helper function that mimics the logic from handleAutoDetectMotifAtu
  const buildSectionCandidates = (sections, paragraphSummaries) => {
    const per = paragraphSummaries?.perSection || {};
    
    return sections
      .map((s) => {
        const key = String(s.text_section);
        const summary = per[key];
        const sectionText = typeof s.text === "string" ? s.text.trim() : "";
        // Use summary if available and not empty, otherwise use original section text
        const textToUse = (typeof summary === "string" && summary.trim()) 
          ? summary.trim() 
          : sectionText;
        return { key, text: textToUse };
      })
      .filter((x) => x.text && x.text.length > 0);
  };

  const checkWholeSummary = (paragraphSummaries) => {
    if (!paragraphSummaries) return false;
    const whole = (paragraphSummaries.whole || "").trim();
    return whole.length > 0;
  };

  it("should use summary when available for a section", () => {
    const sections = [
      {
        text_section: "S0-119",
        text: "这是原文内容，很长很长的一段文字。",
        display_label: "N1"
      }
    ];

    const paragraphSummaries = {
      perSection: {
        "S0-119": "这是摘要内容。\nEnglish: This is a summary."
      },
      whole: ""
    };

    const candidates = buildSectionCandidates(sections, paragraphSummaries);
    
    expect(candidates).toHaveLength(1);
    expect(candidates[0].key).toBe("S0-119");
    expect(candidates[0].text).toBe("这是摘要内容。\nEnglish: This is a summary.");
  });

  it("should use original text when summary is not available", () => {
    const sections = [
      {
        text_section: "S0-119",
        text: "这是原文内容，很长很长的一段文字。",
        display_label: "N1"
      }
    ];

    const paragraphSummaries = {
      perSection: {},
      whole: ""
    };

    const candidates = buildSectionCandidates(sections, paragraphSummaries);
    
    expect(candidates).toHaveLength(1);
    expect(candidates[0].key).toBe("S0-119");
    expect(candidates[0].text).toBe("这是原文内容，很长很长的一段文字。");
  });

  it("should use original text when summary is empty string", () => {
    const sections = [
      {
        text_section: "S0-119",
        text: "这是原文内容，很长很长的一段文字。",
        display_label: "N1"
      }
    ];

    const paragraphSummaries = {
      perSection: {
        "S0-119": ""
      },
      whole: ""
    };

    const candidates = buildSectionCandidates(sections, paragraphSummaries);
    
    expect(candidates).toHaveLength(1);
    expect(candidates[0].key).toBe("S0-119");
    expect(candidates[0].text).toBe("这是原文内容，很长很长的一段文字。");
  });

  it("should use original text when summary is only whitespace", () => {
    const sections = [
      {
        text_section: "S0-119",
        text: "这是原文内容，很长很长的一段文字。",
        display_label: "N1"
      }
    ];

    const paragraphSummaries = {
      perSection: {
        "S0-119": "   \n\t  "
      },
      whole: ""
    };

    const candidates = buildSectionCandidates(sections, paragraphSummaries);
    
    expect(candidates).toHaveLength(1);
    expect(candidates[0].key).toBe("S0-119");
    expect(candidates[0].text).toBe("这是原文内容，很长很长的一段文字。");
  });

  it("should handle mixed case: some sections have summaries, some don't", () => {
    const sections = [
      {
        text_section: "S0-119",
        text: "第一段原文内容。",
        display_label: "N1"
      },
      {
        text_section: "S120-250",
        text: "第二段原文内容。",
        display_label: "N2"
      },
      {
        text_section: "S251-400",
        text: "第三段原文内容。",
        display_label: "N3"
      }
    ];

    const paragraphSummaries = {
      perSection: {
        "S0-119": "第一段摘要。\nEnglish: First summary.",
        // S120-250 has no summary, should use original text
        "S251-400": "第三段摘要。\nEnglish: Third summary."
      },
      whole: ""
    };

    const candidates = buildSectionCandidates(sections, paragraphSummaries);
    
    expect(candidates).toHaveLength(3);
    expect(candidates[0].key).toBe("S0-119");
    expect(candidates[0].text).toBe("第一段摘要。\nEnglish: First summary.");
    expect(candidates[1].key).toBe("S120-250");
    expect(candidates[1].text).toBe("第二段原文内容。");
    expect(candidates[2].key).toBe("S251-400");
    expect(candidates[2].text).toBe("第三段摘要。\nEnglish: Third summary.");
  });

  it("should filter out sections with empty text", () => {
    const sections = [
      {
        text_section: "S0-119",
        text: "有内容的段落。",
        display_label: "N1"
      },
      {
        text_section: "S120-250",
        text: "",
        display_label: "N2"
      },
      {
        text_section: "S251-400",
        text: "   ",
        display_label: "N3"
      }
    ];

    const paragraphSummaries = {
      perSection: {},
      whole: ""
    };

    const candidates = buildSectionCandidates(sections, paragraphSummaries);
    
    expect(candidates).toHaveLength(1);
    expect(candidates[0].key).toBe("S0-119");
  });

  it("should correctly identify when whole summary exists", () => {
    const paragraphSummaries1 = {
      perSection: {},
      whole: "这是完整的摘要。\nEnglish: This is a whole summary."
    };

    const paragraphSummaries2 = {
      perSection: {},
      whole: ""
    };

    const paragraphSummaries3 = {
      perSection: {},
      whole: "   "
    };

    expect(checkWholeSummary(paragraphSummaries1)).toBe(true);
    expect(checkWholeSummary(paragraphSummaries2)).toBe(false);
    expect(checkWholeSummary(paragraphSummaries3)).toBe(false);
  });

  it("should handle real data from CH_002_牛郎织女2_v3.json", () => {
    // Based on actual data from the dataset
    const sections = [
      {
        text_section: "S0-119",
        text: "相传织女是天帝的孙女，或说是王母娘娘的外孙女，这都用不着去管它了 ，总之，是有这么一个仙女，住在银河的东边，用了一种神奇的丝，在织布机上织出了层层叠叠的美丽云彩，随着时间和季节的不同而变幻它们的颜色，叫做\" 天衣\"，意思就是给天做的衣裳。",
        display_label: "N1"
      }
    ];

    const paragraphSummaries = {
      perSection: {
        "S0-119": "相传织女是天帝的孙女或王母娘娘的外孙女，她住在银河东边，用神奇丝线在织布机上织出随季节变幻颜色的美丽云彩，称为‘天衣’。\nEnglish: According to legend, Zhi Nu is the granddaughter of the Heaven Emperor or the niece of the Queen Mother of Heaven. She resides in the east of the Milky Way, weaving beautiful clouds that change colors with the seasons using magical silk on a loom, known as 'heavenly robes'."
      },
      whole: "相传织女是天帝的孙女或王母娘娘的外孙女，居住在银河东岸，用神奇丝线在织布机上编织随季节变幻色彩的云霞，所织云彩被称为‘天衣’。\nEnglish: According to legend, Zhi Nu is the granddaughter of the Heaven Emperor or the niece of the Queen Mother of Heaven. She resides in the east of the Milky Way, weaving clouds that change colors with the seasons using magical silk on a loom, known as 'heavenly robes'."
    };

    const candidates = buildSectionCandidates(sections, paragraphSummaries);
    
    expect(candidates).toHaveLength(1);
    expect(candidates[0].key).toBe("S0-119");
    // Should use summary, not original text
    expect(candidates[0].text).toContain("According to legend");
    expect(candidates[0].text).not.toContain("这都用不着去管它了");
    
    expect(checkWholeSummary(paragraphSummaries)).toBe(true);
  });

  it("should handle real data from CH_003_孟姜女哭长城_v3.json (mixed summaries)", () => {
    // Based on actual data from the dataset
    const sections = [
      {
        text_section: "S0-600",
        text: "秦始皇派卢教寻仙得蝌蚪文，误认'亡秦者胡也'为北方胡人威胁，遂命修长城并传谣捕苏州万喜良以填城。修长城需活人殉葬，引发民忧，官员借童谣传令捉拿万喜良。",
        display_label: "N1"
      },
      {
        text_section: "S601-887",
        text: "童遥的故事可能是虚构的，但苏州确实有位文弱书生万喜良。他因童遥的传言而惊慌，连夜逃离家乡，途中听到关于秦始皇征兵的谣言，最终躲入庄院花园避难。",
        display_label: "N2"
      },
      {
        text_section: "S888-1200",
        text: "这是第三段原文，没有摘要。",
        display_label: "N3"
      }
    ];

    const paragraphSummaries = {
      perSection: {
        "S0-600": "秦始皇派卢教寻仙得蝌蚪文，误认'亡秦者胡也'为北方胡人威胁，遂命修长城并传谣捕苏州万喜良以填城。修长城需活人殉葬，引发民忧，官员借童谣传令捉拿万喜良。\nEnglish: Qin Shi Huang sent Lu Jiao to seek immortals, mistakenly interpreted the scroll's '亡秦者胡也' as a threat from northern barbarians, leading to the Great Wall construction and a rumor to capture Suzhou's Wan Xilang for殉葬. The belief in living sacrifices for eternal fortification caused panic, prompting officials to act on the folk song.",
        "S601-887": "童遥的故事可能是虚构的，但苏州确实有位文弱书生万喜良。他因童遥的传言而惊慌，连夜逃离家乡，途中听到关于秦始皇征兵的谣言，最终躲入庄院花园避难。\nEnglish: The story of Tong Yao might be fictional, but there is indeed a weak scholar named Wan Xilang in Suzhou. Fearing the rumors, he fled his home, heard tales of conscription during the Qin Dynasty, and hid in a farm's garden."
        // S888-1200 has no summary
      },
      whole: ""
    };

    const candidates = buildSectionCandidates(sections, paragraphSummaries);
    
    expect(candidates).toHaveLength(3);
    
    // First section should use summary
    expect(candidates[0].key).toBe("S0-600");
    expect(candidates[0].text).toContain("English: Qin Shi Huang");
    
    // Second section should use summary
    expect(candidates[1].key).toBe("S601-887");
    expect(candidates[1].text).toContain("English: The story of Tong Yao");
    
    // Third section should use original text (no summary available)
    expect(candidates[2].key).toBe("S888-1200");
    expect(candidates[2].text).toBe("这是第三段原文，没有摘要。");
    
    expect(checkWholeSummary(paragraphSummaries)).toBe(false);
  });

  it("should handle edge case: paragraphSummaries is null or undefined", () => {
    const sections = [
      {
        text_section: "S0-119",
        text: "原文内容。",
        display_label: "N1"
      }
    ];

    const candidates1 = buildSectionCandidates(sections, null);
    const candidates2 = buildSectionCandidates(sections, undefined);
    
    expect(candidates1).toHaveLength(1);
    expect(candidates1[0].text).toBe("原文内容。");
    expect(candidates2).toHaveLength(1);
    expect(candidates2[0].text).toBe("原文内容。");
    
    expect(checkWholeSummary(null)).toBe(false);
    expect(checkWholeSummary(undefined)).toBe(false);
  });

  it("should handle edge case: perSection is null or undefined", () => {
    const sections = [
      {
        text_section: "S0-119",
        text: "原文内容。",
        display_label: "N1"
      }
    ];

    const paragraphSummaries1 = { perSection: null, whole: "" };
    const paragraphSummaries2 = { whole: "" };
    
    const candidates1 = buildSectionCandidates(sections, paragraphSummaries1);
    const candidates2 = buildSectionCandidates(sections, paragraphSummaries2);
    
    expect(candidates1).toHaveLength(1);
    expect(candidates1[0].text).toBe("原文内容。");
    expect(candidates2).toHaveLength(1);
    expect(candidates2[0].text).toBe("原文内容。");
  });
});
