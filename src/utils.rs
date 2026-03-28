/// Convert 2-space JSON indentation to 4-space (matches Python json.dump indent=4).
pub fn convert_to_4space_indent(s: &str) -> String {
    let mut result = String::with_capacity(s.len() * 2);
    for line in s.lines() {
        let leading = line.len() - line.trim_start_matches(' ').len();
        let new_leading = leading * 2;
        result.push_str(&" ".repeat(new_leading));
        result.push_str(line.trim_start());
        result.push('\n');
    }
    if !s.ends_with('\n') && result.ends_with('\n') {
        result.pop();
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn indent_conversion_doubles_leading_spaces() {
        let input = "{\n  \"key\": \"value\"\n}";
        let output = convert_to_4space_indent(input);
        assert!(output.contains("    \"key\""), "expected 4-space indent");
    }

    #[test]
    fn indent_conversion_zero_indent_unchanged() {
        assert_eq!(convert_to_4space_indent("{}"), "{}");
        assert_eq!(convert_to_4space_indent("{}\n"), "{}\n");
    }
}
